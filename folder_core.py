"""Editable folder repository. Independent immutable revisions retain concurrent edits.
Yandex Disk is an eventual file transporter, not a distributed lock service.
"""
from __future__ import annotations
import base64,copy,hashlib,json,os,re,shutil,tempfile,uuid,zipfile,time
from datetime import datetime,timezone
from pathlib import Path

def stamp():return datetime.now(timezone.utc).isoformat()
def encode(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
def digest(x):return hashlib.sha256(encode(x)).hexdigest()
def safe(x):
 s=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',str(x)).strip(' .')[:90] or 'Без названия'
 if s.upper().split('.')[0] in {'CON','PRN','AUX','NUL',*('COM'+str(i) for i in range(10)),*('LPT'+str(i) for i in range(10))}:s='_'+s
 return s

def portable_path(value):
 """One representation for repository paths, independent of the host OS."""
 return str(value).replace('\\','/')

def windows_extended_path(value):
 """Absolute Unicode Win32 path, independent of the LongPathsEnabled setting."""
 import ntpath
 value=ntpath.abspath(str(value))
 if value.startswith('\\\\?\\'):return value
 if value.startswith('\\\\'):return '\\\\?\\UNC\\'+value[2:]
 return '\\\\?\\'+value

_WINDOWS_RETRY_DELAYS=(.02,.04,.08,.16,.32,.5,.5,.5)
def retry_windows_file_operation(operation):
 """Retry only Windows sharing/access races; never replace by truncating a file."""
 for attempt in range(len(_WINDOWS_RETRY_DELAYS)+1):
  try:return operation()
  except OSError as exc:
   if getattr(exc,'winerror',None) not in (5,32,33) or attempt==len(_WINDOWS_RETRY_DELAYS):raise
   time.sleep(_WINDOWS_RETRY_DELAYS[attempt])

def atomic(p,data):
 p=Path(windows_extended_path(p) if os.name=='nt' else p)
 p.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.sid-',suffix='.tmp',dir=str(p.parent));tmp=Path(name);original_error=None
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  retry_windows_file_operation(lambda:os.replace(tmp,p))
 except BaseException as exc:
  original_error=exc
  raise
 finally:
  try:retry_windows_file_operation(lambda:tmp.unlink(missing_ok=True))
  except OSError as cleanup_error:
   if original_error is None:raise
   original_error.add_note('Временный файл пока заблокирован: '+str(tmp)+'; '+str(cleanup_error))

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)

def validate_state(s):
 if not isinstance(s,dict) or s.get('meta',{}).get('v')!=30 or not isinstance(s.get('lib'),dict) or not isinstance(s.get('projects'),list):raise ValueError('Неверный формат базы СтройИД')
 for k in ('orgs','people','base','templates','profiles'):
  if not isinstance(s['lib'].get(k),list):raise ValueError('Неверный справочник '+k)
 for p in s['projects']:
  for k in ('systems','materials','journals','surveys','opsDocs'):
   if not isinstance(p.get(k),list):raise ValueError('Неполная структура объекта: '+k)
 return s

LABELS={'projects':'Объекты','executions':'Выполнения','systems':'Системы','materials':'Материалы','acts':'Акты скрытых работ','aik':'Входной контроль','journals':'Журналы','surveys':'Исполнительные съёмки','opsDocs':'Эксплуатация','admin':'Общие документы','sketches':'Исполнительные схемы','trials':'Испытания','orgs':'Организации','people':'Представители','orders':'Приказы и допуски','base':'Материалы и паспорта','profiles':'Профили заказчиков','templates':'Шаблоны Word'}
CHILDREN={'projects':['executions','systems','materials','journals','surveys','opsDocs','admin'],'systems':['acts','aik','journals','sketches','trials']}
IMAGE_FIELDS=('img','photo','logo','sign')

def flatten(s):
 out={}
 def add(field,parent,value,pos):
  v=copy.deepcopy(value);key=field+':'+str(v['id'])
  for f in CHILDREN.get(field,[]):
   for i,c in enumerate(v.pop(f,[])):add(f,key,c,i)
  out[key]={'kind':field,'parent':parent,'field':field,'position':pos,'data':v}
 for i,p in enumerate(s['projects']):add('projects','root',p,i)
 lib=copy.deepcopy(s['lib'])
 for f in LABELS:
  if isinstance(lib.get(f),list):
   for i,v in enumerate(lib.pop(f)):add(f,'root',v,i)
 root={k:copy.deepcopy(v) for k,v in s.items() if k not in ('projects','lib','ui','locks','history','builds','trash','volCfg')};root['lib']=lib
 out['root']={'kind':'root','parent':'','field':'','data':root}
 for k,v in s.get('volCfg',{}).items():out['volume:'+k]={'kind':'volume','parent':'root','field':k,'data':v}
 for f in ('history','builds','trash'):
  for i,v in enumerate(s.get(f,[])):out[f+':'+str(v.get('id') or digest(v))]={'kind':f,'parent':'root','field':f,'position':i,'data':copy.deepcopy(v)}
 return out

class Store:
 def __init__(self,root):
  self.root=Path(root).resolve();self.events_dir=self.root/'Служебные данные'/'Версии карточек';self.backups=self.root/'Резервные копии'/'Снимки';self.blobs=self.root/'Резервные копии'/'Файлы по содержимому';self.files=self.root/'Входящие документы'
  for p in (self.events_dir,self.backups,self.blobs,self.files):p.mkdir(parents=True,exist_ok=True)
  self.actor=os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'ПК';self.events={};self.heads={};self.latest={};self.paths={};self.baseline={};self.base_heads={};self.materialized={};self.invalid=set();self.warnings=[];self.conflicts=[];self.ui={};self.ready=False;self.revision=0;self.last_checkpoint=None
  self._migrate()
 def path(self,rel):
  p=(self.root/portable_path(rel)).resolve()
  if not p.is_relative_to(self.root):raise ValueError('Путь выходит за папку базы')
  return p
 @staticmethod
 def hash_file(p):
  h=hashlib.sha256()
  with open(p,'rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  return h.hexdigest()
 def _blob(self,p):
  sha=self.hash_file(p);dest=self.blobs/sha
  if not dest.exists():atomic(dest,Path(p).read_bytes())
  return sha
 def _read_json(self,p):return json.loads(p.read_text('utf-8-sig'))
 def _scan(self):
  events={}
  for p in self.events_dir.glob('*.json'):
   try:
    e=dict(self._read_json(p))
    e['path']=portable_path(e.get('path',''))
    if not isinstance(e,dict) or not all(k in e for k in ('id','key','parents','record','path')):raise ValueError('неполная версия')
    if not re.fullmatch('[0-9a-f]{32}',e['id']) or not isinstance(e['parents'],list):raise ValueError('неверный идентификатор')
    if e['record'] is not None and (not isinstance(e['record'],dict) or not isinstance(e['record'].get('data'),dict)):raise ValueError('неверная карточка')
    self.path(e['path']);events[e['id']]=e
   except Exception as ex:self.warnings.append({'path':str(p.relative_to(self.root)),'message':'Не прочитана версия карточки: '+str(ex)})
  self.events=events;self.heads={};self.latest={};self.paths={};self.conflicts=[];consumed={p for e in events.values() for p in e['parents']}
  for e in events.values():
   if e['id'] not in consumed:self.heads.setdefault(e['key'],[]).append(e['id'])
  for key,ids in self.heads.items():
   choices=[events[i] for i in ids];e=max(choices,key=lambda x:(x.get('ts',''),x['id']));self.latest[key]=e['record'];self.paths[key]=e['path']
   if any(p not in events for c in choices for p in c['parents']):self.warnings.append({'key':key,'path':e['path'],'message':'Ожидаются связанные версии. Дождитесь синхронизации Яндекс Диска.'})
   if len({digest(c['record']) for c in choices})>1:self.conflicts.append({'key':key,'path':e['path'],'versions':[{'id':c['id'],'by':c.get('by',''),'ts':c.get('ts',''),'record':c['record']} for c in choices]})
 def _emit(self,key,r,parents,path):
  e={'id':uuid.uuid4().hex,'key':key,'parents':list(parents),'record':r,'path':portable_path(path),'by':self.actor,'ts':stamp()};atomic(self.events_dir/(e['id']+'.json'),encode(e));self.events[e['id']]=e
 def _title(self,r):
  d=r['data'];return d.get('short') or d.get('name') or d.get('num') or d.get('fioShort') or d.get('code') or LABELS.get(r['field'],'Карточка')
 def _record_path(self,key,r,records):
  if key in self.paths:return self.paths[key]
  if key=='root':return 'Настройки/База.json'
  kind=r['kind'];suffix=hashlib.sha256(key.encode()).hexdigest()[:6]
  if kind in ('history','builds','trash','volume'):return 'Настройки/'+{'history':'История','builds':'Сборки','trash':'Корзина','volume':'Настройки томов'}[kind]+'/'+suffix+'.json'
  parent=r['parent']
  if parent=='root':base=Path('Объекты') if kind=='projects' else Path('Справочники')/LABELS.get(kind,kind)
  else:
   pr=records.get(parent) or self.latest.get(parent);base=Path(self._record_path(parent,pr,records)).parent/LABELS.get(kind,kind)
  if kind in ('people','orders') and r['data'].get('orgId'):
   orgkey='orgs:'+r['data']['orgId'];org=records.get(orgkey) or self.latest.get(orgkey)
   if org:base=Path(self._record_path(orgkey,org,records)).parent/LABELS[kind]
  return portable_path(base/(safe(self._title(r))+' ['+suffix+']')/('Материал.json' if kind in ('materials','base') else 'Карточка.json'))
 def _validate_card(self,new,r):
  old=r['data']
  def check(n,o,label):
   if isinstance(o,dict):
    if not isinstance(n,dict):raise ValueError('Поле '+label+' должно быть объектом')
    for k,v in o.items():
     if k not in n:raise ValueError('Нет поля '+label+'.'+k)
     check(n[k],v,label+'.'+k)
   elif isinstance(o,list):
    if not isinstance(n,list):raise ValueError('Поле '+label+' должно быть списком')
    oldmap={str(x.get('id')):x for x in o if isinstance(x,dict)}
    for item in n:
     sample=oldmap.get(str(item.get('id'))) if isinstance(item,dict) else None
     if sample is not None:check(item,sample,label)
     elif o and not isinstance(item,type(o[0])):raise ValueError('Неверная строка списка '+label)
   elif isinstance(o,str) and not isinstance(n,str):raise ValueError('Поле '+label+' должно быть строкой')
   elif isinstance(o,(int,float)) and not isinstance(n,(int,float)):raise ValueError('Поле '+label+' должно быть числом')
  check(new,old,'Карточка')
  if old.get('id') and new.get('id')!=old['id']:raise ValueError('Не изменяйте поле id')
  if r['kind'] in ('materials','base'):
   for d in new.get('docs',[]):
    if not isinstance(d,dict) or any(not isinstance(d.get(k),str) for k in ('id','type','num','date','file')):raise ValueError('В документе качества нужны поля id, type, num, date, file')
 def _disk_changes(self):
  self.invalid=set()
  for key,r in list(self.latest.items()):
   if r is None:continue
   p=self.path(self.paths[key])
   if not p.exists():continue
   try:
    v=self._read_json(p)
    if v==r['data'] or any(e['key']==key and e['record'] and e['record']['data']==v for e in self.events.values()):continue
    self._validate_card(v,r);updated=copy.deepcopy(r);updated['data']=v;self._emit(key,updated,self.materialized.get(key,self.heads[key]),self.paths[key])
   except Exception as ex:
    self.invalid.add(key);detail='Неверный синтаксис: строка '+str(ex.lineno)+', столбец '+str(ex.colno) if isinstance(ex,json.JSONDecodeError) else str(ex)
    self.warnings.append({'key':key,'path':self.paths[key],'message':'Повреждён JSON: '+detail})
 @staticmethod
 def _image(p):return 'data:image/'+('png' if Path(p).suffix.lower()=='.png' else 'jpeg')+';base64,'+base64.b64encode(Path(p).read_bytes()).decode()
 @staticmethod
 def _pages(p):
  if Path(p).suffix.lower()!='.pdf':return 0
  try:
   from pypdf import PdfReader
   return len(PdfReader(p).pages)
  except Exception:return 0
 def _files_in(self,folder):return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ('.pdf','.docx','.doc','.xlsx','.xls','.png','.jpg','.jpeg','.dwg') and not p.name.startswith(('~$','.'))]
 def _discover(self):
  known={str(self.path(e['path']).parent) for e in self.events.values()};locations=[('root','base',self.root/'Справочники'/'Материалы и паспорта'),('root','templates',self.root/'Справочники'/'Шаблоны Word')]
  for key,r in self.latest.items():
   if r:
    for field in CHILDREN.get(r['kind'],[]):
     if field!='systems':locations.append((key,field,self.path(self.paths[key]).parent/LABELS[field]))
  for parent,field,base in locations:
   base.mkdir(parents=True,exist_ok=True)
   for folder in list(base.iterdir()):
    if folder.is_dir() and str(folder.resolve()) not in known and self._files_in(folder):name=folder.name
    elif folder.is_file() and folder.suffix.lower() in ('.pdf','.docx','.doc','.xlsx','.xls','.png','.jpg','.jpeg','.dwg'):
     name=folder.stem;target=base/safe(name)
     if target.exists():continue
     target.mkdir();shutil.move(folder,target/folder.name);folder=target
    else:continue
    ident='auto'+hashlib.sha256(str(folder.relative_to(self.root)).encode()).hexdigest()[:20];v={'id':ident,'name':name}
    if field in ('base','materials'):v.update(baseId='',category='',brand='',maker='',note='',docs=[])
    elif field=='templates':v.update(type='Иной документ',section='other',tags=[],file='',fileKey='',date='',locked=False)
    elif field=='acts':v.update(type='АОСР',num=name,date='',works=name,place='',start='',end='',rd='',norms='',next='',materials=[],aikLinks={},subs=[],signers={},schemes=[],tests=[],photos=[],scan={'file':'','pages':0},rev=1,photoLayout=2,note='',status='В работе',remarks=[],schemeLinks=[],testLinks=[])
    elif field=='journals':v.update(kind='Специальный журнал',mode='B',file='',pages=0,cols=[],rows=[])
    elif field=='aik':v.update(num=name,date='',materialId='',qty='',note='',file='',pages=0)
    else:v.update(num='',date='',file='',pages=0,note='')
    key=field+':'+ident;r={'kind':field,'parent':parent,'field':field,'data':v,'position':100000};path=folder/('Материал.json' if field in ('base','materials') else 'Карточка.json')
    if key not in self.latest:self._emit(key,r,[],path.relative_to(self.root))
 def _adopt_files(self):
  conflict={c['key'] for c in self.conflicts}
  for key,r in list(self.latest.items()):
   if r is None or key in self.invalid or key in conflict:continue
   v=copy.deepcopy(r['data']);folder=self.path(self.paths[key]).parent
   if not folder.exists():continue
   changed=False
   for node in walk(v):
    rel=node.get('fileKey')
    if not rel:continue
    p=self.path(rel)
    if not p.is_file():continue
    sha=self.hash_file(p)
    if sha==node.get('fileHash'):continue
    known={a.get('fileHash') for e in self.events.values() if e['key']==key and e['record'] for a in walk(e['record']['data']) if a.get('fileKey')==rel}
    if sha in known:continue
    node['fileHash']=self._blob(p);changed=True
    if p.suffix.lower()=='.pdf':node['pages']=self._pages(p)
    if r['kind']=='templates' and p.suffix.lower()=='.docx':
     from word_templates import inspect_docx
     try:node['tags']=inspect_docx(p.read_bytes())['tags']
     except ValueError as ex:self.warnings.append({'key':key,'path':rel,'message':'Шаблон Word повреждён: '+str(ex)})
   locations=[(folder,None)]+[(folder/name,field) for field,name in {'schemes':'Схемы к акту','tests':'Испытания к акту','photos':'Фотографии','attachments':'Дополнительные документы'}.items() if (folder/name).exists()]
   for loc,field in locations:
    for p in self._files_in(loc):
     rel=p.relative_to(self.root).as_posix()
     if any(n.get('fileKey')==rel for n in walk(v)):continue
     if any(e['key']==key and e['record'] and any(n.get('fileKey')==rel for n in walk(e['record']['data'])) for e in self.events.values()):continue
     info={'id':'f'+hashlib.sha256(rel.encode()).hexdigest()[:16],'name':p.stem,'file':p.name,'fileKey':rel,'fileHash':self._blob(p),'num':'','date':'','pages':self._pages(p)}
     if r['kind'] in ('materials','base'):
      info['type']='Паспорт' if 'паспорт' in p.stem.lower() else 'Декларация о соответствии' if 'деклар' in p.stem.lower() else 'Сертификат соответствия';v.setdefault('docs',[]).append(info)
     elif field:
      if field=='photos' and p.suffix.lower() in ('.png','.jpg','.jpeg'):info.update(cap=p.stem,img=rel)
      v.setdefault(field,[]).append(info)
     elif r['kind']=='acts' and p.suffix.lower()=='.pdf' and not v.get('scan',{}).get('fileKey'):v['scan']=info
     elif r['kind'] in ('aik','journals','sketches','trials','surveys','opsDocs','admin','orders','templates') and not v.get('fileKey'):
      v.update({k:info[k] for k in ('file','fileKey','fileHash','pages')})
      if r['kind']=='journals':v['mode']='B'
      if r['kind']=='templates' and p.suffix.lower()=='.docx':
       from word_templates import inspect_docx
       try:v['tags']=inspect_docx(p.read_bytes())['tags']
       except ValueError:v['tags']=[]
     else:v.setdefault('attachments',[]).append(info)
     changed=True
   if changed:nr=copy.deepcopy(r);nr['data']=v;self._emit(key,nr,self.heads[key],self.paths[key])
 def _materialize(self):
  blocked=self.invalid|{c['key'] for c in self.conflicts}
  for key,r in self.latest.items():
   if r is None or key in blocked:continue
   path=self.path(self.paths[key]);content=encode(r['data'])
   for node in walk(r['data']):
    rel=node.get('fileKey') or node.get('photoKey');sha=node.get('fileHash') or node.get('photoHash')
    if not rel:continue
    target=self.path(rel)
    if not target.exists() or sha and self.hash_file(target)!=sha:
     blob=self.blobs/str(sha)
     if sha and blob.is_file() and self.hash_file(blob)==sha:atomic(target,blob.read_bytes())
     else:self.warnings.append({'key':key,'path':rel,'message':'Ожидается файл выбранной версии. Проверьте синхронизацию Яндекс Диска.'})
   if not path.exists() or path.read_bytes()!=content:atomic(path,content)
   self.materialized[key]=list(self.heads[key])
   for field in CHILDREN.get(r['kind'],[]):(path.parent/LABELS[field]).mkdir(exist_ok=True)
   if r['kind']=='acts':
    for name in ('Схемы к акту','Испытания к акту','Фотографии'):(path.parent/name).mkdir(exist_ok=True)
  for key,r in self.latest.items():
   if r is None:
    p=self.path(self.paths[key])
    if p.exists():dest=self.root/'Корзина файлов'/uuid.uuid4().hex/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(p,dest)
 def _assemble(self,records=None,hydrate=True):
  records=records if records is not None else self.latest;root=records.get('root')
  if not root:return None
  s=copy.deepcopy(root['data']);s.update(projects=[],ui=copy.deepcopy(self.ui),locks={},history=[],builds=[],trash=[],volCfg={})
  for field in ('orgs','people','orders','base','profiles','templates'):s['lib'][field]=[]
  objs={}
  for key,r in records.items():
   if r is None or key=='root':continue
   objs[key]=copy.deepcopy(r['data'])
   for f in CHILDREN.get(r['kind'],[]):objs[key][f]=[]
  for key,v in sorted(objs.items(),key=lambda kv:(records[kv[0]].get('position',100000),kv[0])):
   r=records[key];kind=r['kind'];field=r['field'];parent=r['parent']
   if kind=='volume':s['volCfg'][field]=v
   elif kind in ('history','builds','trash'):s[field].append(v)
   elif parent=='root':(s if field=='projects' else s['lib']).setdefault(field,[]).append(v)
   elif parent in objs:objs[parent].setdefault(field,[]).append(v)
   else:self.warnings.append({'key':key,'path':self.paths.get(key,key),'message':'Ожидается родительская карточка'})
  if hydrate:
   for node in walk(s):
    for field in IMAGE_FIELDS:
     value=node.get(field)
     if isinstance(value,str) and value and not value.startswith('data:'):
      try:
       p=self.path(value)
       if p.is_file():node[field]=self._image(p)
      except ValueError:pass
  return s
 def load(self):
  self.warnings=[];self._scan();self._disk_changes();self._scan();self._discover();self._scan();self._adopt_files();self._scan();self._materialize();s=self._assemble()
  self.warnings=list({(w.get('key',''),w['path'],w['message']):w for w in self.warnings}.values());self.baseline=copy.deepcopy(self.latest);self.base_heads=copy.deepcopy(self.heads);self.ready=True;self.revision+=1
  return {'state':s,'revision':self.revision,'root':str(self.root),'warnings':self.warnings,'conflicts':self.conflicts}
 def _place(self,r,path):
  folder=self.path(path).parent;folder.mkdir(parents=True,exist_ok=True)
  for node in walk(r['data']):
   key=node.get('fileKey')
   if key:
    try:p,name=self.asset_path(key)
    except ValueError:continue
    sha=self.hash_file(p)
    if node.get('fileHash') and sha!=node['fileHash'] and not p.is_relative_to(self.files):
     # Preserve a remotely selected source while its physical file is still in transit.
     pass
    else:node['fileHash']=self._blob(p)
    if p.is_relative_to(self.files) or r['kind']=='materials' and not p.is_relative_to(folder):
     target=folder/safe(name)
     if target.exists() and self.hash_file(target)!=sha:target=folder/(safe(Path(name).stem)+' ('+sha[:10]+')'+Path(name).suffix)
     if not target.exists():atomic(target,p.read_bytes())
     node.update(file=target.name,fileKey=target.relative_to(self.root).as_posix())
   for field in IMAGE_FIELDS:
    value=node.get(field)
    if isinstance(value,str) and value.startswith('data:image/'):
     try:
      raw=base64.b64decode(value.split(',',1)[1]);ext='.png' if 'image/png' in value[:30] else '.jpg';name=safe(node.get('cap') or ('Фото объекта' if field=='photo' else 'Фото' if field=='img' else field));p=folder/(name+ext)
      if p.exists() and p.read_bytes()!=raw:p=folder/(name+' ('+hashlib.sha256(raw).hexdigest()[:10]+')'+ext)
      if not p.exists():atomic(p,raw)
      rel=p.relative_to(self.root).as_posix();node[field]=rel;sha=self._blob(p)
      if field=='img':node.update(file=p.name,fileKey=rel,fileHash=sha)
      elif field=='photo':node.update(photoKey=rel,photoHash=sha)
      else:node[field+'Key']=rel;node[field+'Hash']=sha
     except (ValueError,IndexError):pass
 def save(self,state,expected_revision):
  validate_state(state)
  if not self.ready:self.load()
  before=copy.deepcopy(self.baseline);parents=copy.deepcopy(self.base_heads);self.ui=copy.deepcopy(state.get('ui',{}));records=flatten(state);self._scan()
  blocked={c['key'] for c in self.conflicts}
  # Only rename projections when this writer owns the current card head.
  for key,r in records.items():
   old=before.get(key)
   if not old or key not in self.paths or key in blocked or key in self.invalid or r['kind'] in ('root','history','builds','trash','volume'):continue
   if self._title(old)==self._title(r):continue
   folder=self.path(self.paths[key]).parent;dest=folder.with_name(safe(self._title(r))+' ['+hashlib.sha256(key.encode()).hexdigest()[:6]+']')
   if folder==dest or dest.exists():continue
   if folder.exists():shutil.move(folder,dest)
   a=folder.relative_to(self.root).as_posix()+'/';b=dest.relative_to(self.root).as_posix()+'/'
   for k,p in list(self.paths.items()):
    p=Path(p).as_posix()
    if p.startswith(a):self.paths[k]=b+p[len(a):]
   for rec in records.values():
    for node in walk(rec['data']):
     for f in ('fileKey','photoKey','logoKey','signKey',*IMAGE_FIELDS):
      if isinstance(node.get(f),str) and node[f].startswith(a):node[f]=b+node[f][len(a):]
  changes=[]
  for key in set(before)|set(records):
   r=records.get(key);path=self.paths.get(key) or self._record_path(key,r,records)
   if r:self._place(r,path)
   if r==before.get(key) and all(self.events[i]['path']==path for i in parents.get(key,[]) if i in self.events):continue
   if key in self.invalid:raise ValueError('Сначала восстановите повреждённую карточку: '+path)
   if key in blocked:raise ValueError('Сначала разрешите конфликт карточки: '+path)
   changes.append((key,r,parents.get(key,[]),path))
  for args in changes:self._emit(*args)
  return self.load()
 def import_file(self,source,name=None):
  source=Path(source)
  if not source.is_file():raise ValueError('Файл не найден')
  dest=self.files/uuid.uuid4().hex/safe(name or source.name);atomic(dest,source.read_bytes());return {'id':dest.relative_to(self.root).as_posix(),'name':name or source.name,'sha256':self._blob(dest),'size':dest.stat().st_size,'created':stamp()}
 def asset_path(self,key):
  p=self.path(key)
  if not p.is_file():raise ValueError('Файл отсутствует или ещё не синхронизирован: '+str(key))
  return p,p.name
 def repair(self,key,data):
  self._scan();r=self.latest.get(key)
  if not r:raise ValueError('Карточка не найдена')
  self._validate_card(data,r);r=copy.deepcopy(r);r['data']=data;p=self.path(self.paths[key])
  if p.exists():atomic(self.root/'Повреждённые JSON'/(uuid.uuid4().hex[:8]+'_'+p.name),p.read_bytes())
  self._emit(key,r,self.heads[key],self.paths[key]);atomic(p,encode(data));return self.load()
 def resolve(self,key,version):
  self._scan()
  if version not in self.heads.get(key,[]):raise ValueError('Версии изменились. Обновите список конфликтов.')
  e=self.events[version];self._emit(key,e['record'],self.heads[key],e['path'])
  if e['record']:atomic(self.path(e['path']),encode(e['record']['data']))
  return self.load()
 def _checkpoint(self,reason):
  if not self.latest.get('root'):raise ValueError('Нет данных для резервной копии')
  # Snapshots reference deduplicated JSON cards and binaries; no repeated full-library copies.
  records={};assets={}
  for key,r in self.latest.items():
   if r is None:continue
   sha=digest(r);blob=self.blobs/sha
   if not blob.exists():atomic(blob,encode(r))
   records[key]=sha
   for n in walk(r['data']):
    for field in ('file','photo','logo','sign'):
     rel=n.get(field+'Key');sha=n.get(field+'Hash')
     if not rel:continue
     p=self.path(rel)
     if p.is_file():
      actual=self._blob(p)
      if sha and actual!=sha:raise ValueError('Файл ещё не синхронизирован: '+rel)
      assets[rel]=actual
  content={'records':records,'assets':assets};sig=digest(content)
  if reason=='Автоматически' and sig==self.last_checkpoint:return None
  self.last_checkpoint=sig;snap={'format':'stroiid-folders-2','ts':stamp(),'reason':reason,'sha256':sig,**content};name=datetime.now().strftime('%Y%m%d-%H%M%S')+'_'+uuid.uuid4().hex[:8]+'.json';atomic(self.backups/name,encode(snap));return {'id':name,'ts':snap['ts'],'reason':reason,'path':str(self.backups/name)}
 def backup(self,reason='Вручную',state=None):
  if state:self.save(state,self.revision)
  return self._checkpoint(reason)
 def list_backups(self):
  out=[]
  for p in sorted(self.backups.glob('*.json'),reverse=True):
   try:
    s=json.loads(p.read_text('utf-8'));out.append({'id':p.name,'ts':s['ts'],'reason':s['reason'],'path':str(p)})
   except Exception:continue
  return out
 def export_backup(self,key,target):
  p=self.backups/Path(key).name;s=json.loads(p.read_text('utf-8'));hashes=set(s['records'].values())|set(s['assets'].values())
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('snapshot.json',encode(s))
   for sha in hashes:z.write(self.blobs/sha,'files/'+sha)
 def _legacy(self,z):
  m=json.loads(z.read('manifest.json'));raw=z.read('state.json')
  if m.get('format')!='stroiid-backup-1' or hashlib.sha256(raw).hexdigest()!=m['state_sha256']:raise ValueError('Повреждена старая копия')
  s=validate_state(json.loads(raw));mapping={};verified=[];names={'manifest.json','state.json'}
  for a in m['assets']:
   if not re.fullmatch('[0-9a-f]{32}',a['id']):raise ValueError('Неверное вложение')
   name='files/'+a['id'];data=z.read(name);names.add(name)
   if len(data)!=a['size'] or hashlib.sha256(data).hexdigest()!=a['sha256']:raise ValueError('Повреждено вложение')
   verified.append((a,data))
  if set(z.namelist())!=names or len(z.namelist())!=len(set(z.namelist())):raise ValueError('Лишние пути в архиве')
  self.load()
  if self.latest.get('root'):self._checkpoint('Перед восстановлением')
  with tempfile.TemporaryDirectory() as folder:
   for a,data in verified:
    p=Path(folder)/safe(a['name']);p.write_bytes(data);mapping[a['id']]=self.import_file(p)['id']
  for n in walk(s):
   if 'fileKey' in n:n['fileKey']=mapping.get(n['fileKey'],n['fileKey'])
  s['ui']=copy.deepcopy(self.ui);return self.save(s,self.revision)
 def restore(self,archive_path):
  p=Path(archive_path)
  if p.suffix.lower()=='.zip':
   with zipfile.ZipFile(p) as z:
    if sum(x.file_size for x in z.infolist())>4*1024**3:raise ValueError('Копия слишком велика')
    if 'snapshot.json' not in z.namelist():return self._legacy(z)
    snap=json.loads(z.read('snapshot.json'));hashes=set(snap['records'].values())|set(snap['assets'].values());expected={'snapshot.json'}|{'files/'+h for h in hashes}
    if set(z.namelist())!=expected or len(z.namelist())!=len(set(z.namelist())):raise ValueError('Лишние пути в архиве')
    contents={h:z.read('files/'+h) for h in hashes}
    for h,data in contents.items():
     if not re.fullmatch('[0-9a-f]{64}',h) or hashlib.sha256(data).hexdigest()!=h:raise ValueError('Повреждён файл копии')
    for h,data in contents.items():atomic(self.blobs/h,data)
  else:snap=json.loads(p.read_text('utf-8'))
  if snap.get('format')!='stroiid-folders-2' or digest({'records':snap['records'],'assets':snap['assets']})!=snap.get('sha256'):raise ValueError('Повреждена резервная копия')
  records={}
  for key,h in snap['records'].items():
   if not re.fullmatch('[0-9a-f]{64}',h) or self.hash_file(self.blobs/h)!=h:raise ValueError('Повреждена карточка копии')
   records[key]=json.loads((self.blobs/h).read_text('utf-8'))
  state=validate_state(self._assemble(records,hydrate=False))
  for rel,h in snap['assets'].items():
   self.path(rel)
   if not re.fullmatch('[0-9a-f]{64}',h) or self.hash_file(self.blobs/h)!=h:raise ValueError('Повреждено вложение копии')
  current=self.load()
  if current['conflicts']:raise ValueError('Сначала разрешите конфликты')
  if current['state']:self._checkpoint('Перед восстановлением')
  for rel,h in snap['assets'].items():
   dest=self.path(rel)
   if dest.exists():self._blob(dest)
   atomic(dest,(self.blobs/h).read_bytes())
  for key in list(self.invalid):
   if key in records:self.repair(key,records[key]['data'])
  state['ui']=copy.deepcopy(self.ui);return self.save(state,self.revision)
 def _migrate(self):
  p=self.root/'stroiid.sqlite3'
  if not p.exists() or any(self.events_dir.glob('*.json')):return
  import sqlite3
  db=sqlite3.connect(p);row=db.execute('SELECT payload FROM workspace WHERE id=1').fetchone()
  if not row:db.close();return
  s=validate_state(json.loads(row[0]));mapping={}
  for key,name in db.execute('SELECT id,name FROM assets'):
   path=self.root/'files'/key
   if path.is_file():mapping[key]=self.import_file(path,name)['id']
  db.close()
  for n in walk(s):
   if 'fileKey' in n:n['fileKey']=mapping.get(n['fileKey'],n['fileKey'])
  self.load();self.save(s,self.revision);atomic(self.root/'ПЕРЕНОС ИЗ ПРЕЖНЕЙ ВЕРСИИ.txt','Карточки перенесены в JSON. Прежние stroiid.sqlite3 и files сохранены для проверки.\n'.encode())
 def close(self):pass
