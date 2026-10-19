"""Readable project hierarchy, recoverable deletion and portable export support."""
import copy,json,hashlib,re,shutil,uuid,zipfile
from pathlib import Path
from folder_core import Store as CoreStore, LABELS, CHILDREN, walk, atomic, encode, digest, safe, validate_state, stamp, portable_path
from model_v8 import migrate

from storage_speed import FastFiles
from card_history import CardHistory

class Store(CardHistory,FastFiles,CoreStore):
 def __init__(self,root):
  self._hash_cache={};self._json_cache={};self.metrics={'hashed_files':0,'parsed_json':0,'loads':0,'saves':0}
  root=Path(root).resolve();service=root/'_Служебное';service.mkdir(parents=True,exist_ok=True)
  for old,new in [('Служебные данные/Версии карточек','Версии карточек'),('Резервные копии/Снимки','Резервные копии/Снимки'),('Резервные копии/Файлы по содержимому','Резервные копии/Файлы по содержимому'),('Входящие документы','Входящие документы')]:
   src=root/old;dest=service/new
   if src.exists():
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.move(src,dest)
    else:
     for f in src.rglob('*'):
      if f.is_file():target=dest/f.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
     shutil.rmtree(src)
  self.service=service;self.events_dir=service/'Версии карточек';self.backups=service/'Резервные копии'/'Снимки';self.blobs=service/'Резервные копии'/'Файлы по содержимому';self.files=service/'Входящие документы'
  # Core init is reproduced to avoid recreating its obsolete top-level folders.
  import os
  self.root=root
  for p in (self.events_dir,self.backups,self.blobs,self.files):p.mkdir(parents=True,exist_ok=True)
  self.actor=os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'ПК';self.events={};self.heads={};self.latest={};self.paths={};self.baseline={};self.base_heads={};self.materialized={};self.invalid=set();self.warnings=[];self.conflicts=[];self.ui={};self.ready=False;self.revision=0;self.last_checkpoint=None
  self._loading=False;self._saving=False;self._records={};self.missing={};self.force=set()
  self.ledger_path=service/'Проекция.json'
  try:
   self.known=json.loads(self.ledger_path.read_text('utf-8'))
   self.known={k:{**v,'files':[portable_path(f) for f in v.get('files',[])]} for k,v in self.known.items()}
  except (OSError,ValueError,TypeError,AttributeError):self.known={}
  self._migrate()
  self._archive_previous()
 def _archive_previous(self):
  if not self.latest.get('root') or self.latest['root']['data'].get('meta',{}).get('folderModel',0)<8:return
  active={Path(self.paths[k]).parts[0].casefold() for k,r in self.latest.items() if r and r['kind']=='projects'}
  for name in ('Объекты','Настройки','Служебные данные','Резервные копии','files','stroiid.sqlite3','stroiid.sqlite3-wal','stroiid.sqlite3-shm','ПЕРЕНОС ИЗ ПРЕЖНЕЙ ВЕРСИИ.txt'):
   old=self.root/name
   if not old.exists() or name.casefold() in active:continue
   dest=self.service/'Предыдущая структура'/name;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():dest=dest.with_name(dest.name+' ('+uuid.uuid4().hex[:8]+')')
   shutil.move(old,dest)
 def _record_path(self,key,r,records):
  if key=='root':return '_Служебное/Настройки/База.json'
  kind=r['kind'];d=r['data']
  if kind in ('history','builds','volume'):return '_Служебное/Настройки/'+{'history':'История','builds':'Сборки','volume':'Составы'}[kind]+'/'+hashlib.sha256(key.encode()).hexdigest()[:16]+'.json'
  if kind=='trash':return portable_path(Path('_Служебное/Корзина')/(safe(d.get('name') or self._title(r))+' ('+safe(d['id'])[:20]+')')/'Удалённое.json')
  def display(x):
   v=x['data'];return safe((v.get('code')+' — '+v.get('name','')) if x['kind']=='systems' and v.get('code') else self._title(x))
  def sibling_name(parent,name):
   def group(x):
    v=x['data']
    return (x.get('parent'),v.get('executionId') if kind=='systems' else v.get('orgId') if kind in ('people','orders') else '')
   peers=sorted(k for k,x in records.items() if x and x.get('kind')==kind and group(x)==group(r) and display(x).casefold()==name.casefold())
   assigned={};used=set()
   for k in peers:
    previous=Path(str(self.paths.get(k,'')).replace('\\','/')).parent.name
    if (previous.casefold()==name.casefold() or re.fullmatch(re.escape(name)+r' \([2-9]\d*\)|'+re.escape(name)+r' \(1\d+\)',previous,re.I)) and previous.casefold() not in used:
     assigned[k]=previous;used.add(previous.casefold())
   for k in peers:
    if k in assigned:continue
    index=1;candidate=name
    while candidate.casefold() in used:
     index+=1;candidate=name+' ('+str(index)+')'
    assigned[k]=candidate;used.add(candidate.casefold())
   return assigned.get(key,name)
  parent=r['parent'];name=safe((d.get('code')+' — '+d.get('name','')) if kind=='systems' and d.get('code') else self._title(r));name=sibling_name(parent,name)
  if kind=='projects':
   base=Path()
   if name.casefold() in ('_служебное','справочники'):name+=' (объект)'
  elif kind=='executions':base=Path(self._record_path(parent,records[parent],records)).parent
  elif kind=='systems':
   ek='executions:'+d.get('executionId','');pr=records.get(ek)
   base=Path(self._record_path(ek,pr,records)).parent if pr else Path(self._record_path(parent,records[parent],records)).parent/'Выполнение 1'
  elif parent=='root':
   section={'base':'Материалы и паспорта','orgs':'Организации и подписанты','people':'Организации и подписанты/Представители','orders':'Организации и подписанты/Приказы','profiles':'Профили и шаблоны/Профили','templates':'Профили и шаблоны/Шаблоны Word'}.get(kind,LABELS.get(kind,kind));base=Path('Справочники')/section
   if kind in ('people','orders') and d.get('orgId'):
    ok='orgs:'+d['orgId']
    if records.get(ok):base=Path(self._record_path(ok,records[ok],records)).parent/LABELS[kind]
  else:
   pr=records.get(parent) or self.latest.get(parent);base=Path(self._record_path(parent,pr,records)).parent
   if pr['kind']=='projects':base/='Общие документы'
   base/=LABELS.get(kind,kind)
  filename='Материал.json' if kind in ('materials','base') else 'Карточка.json'
  return portable_path(base/name/filename)
 def _disk_changes(self):
  super()._disk_changes();self.missing={}
  for key,r in self.latest.items():
   known=self.known.get(key)
   if not r or not known:continue
   rel=self.paths[key]
   candidates=[rel]+[n.get(f) for n in walk(r['data']) for f in ('fileKey','photoKey','logoKey','signKey') if n.get(f)]
   absent=[p for p in candidates if p in known.get('files',[]) and not self.path(p).is_file()]
   if absent and key not in self.force:
    self.missing[key]=absent
    for p in absent:self.warnings.append({'key':key,'path':p,'message':'Файл отсутствует: удалён через Проводник или ещё не синхронизирован. Можно восстановить сохранённую версию.','missing':True})
 def _discover(self):
  # Retain document discovery from Explorer while avoiding false system/card imports.
  known={str(self.path(e['path']).parent) for e in self.events.values()};locations=[('root','base',self.root/'Справочники/Материалы и паспорта'),('root','templates',self.root/'Справочники/Профили и шаблоны/Шаблоны Word')]
  for key,r in self.latest.items():
   if r and r['kind'] not in ('root','trash'):
    for field in CHILDREN.get(r['kind'],[]):
     if field not in ('systems','executions','materials'):locations.append((key,field,self.path(self.paths[key]).parent/LABELS[field]))
  # Core discover is reused with redirected locations through a short isolated implementation.
  for parent,field,base in locations:
   if not base.exists():continue
   for folder in list(base.iterdir()):
    if not folder.is_dir() or str(folder.resolve()) in known or not self._files_in(folder):continue
    ident='auto'+hashlib.sha256(str(folder.relative_to(self.root)).encode()).hexdigest()[:20];v={'id':ident,'name':folder.name,'num':'','date':'','file':'','pages':0,'note':''}
    if field=='base':v.update(baseId='',category='',brand='',maker='',docs=[])
    elif field=='templates':v.update(type='Иной документ',section='other',tags=[],fileKey='',locked=False)
    elif field=='journals':v.update(kind='Специальный журнал',mode='B',cols=[],rows=[])
    elif field=='acts':continue
    key=field+':'+ident;r={'kind':field,'parent':parent,'field':field,'data':v,'position':100000};path=folder/('Материал.json' if field=='base' else 'Карточка.json')
    if key not in self.latest:self._emit(key,r,[],path.relative_to(self.root))
 def _materialize(self):
  self._sync_history()
  saved_invalid=self.invalid;self.invalid=self.invalid|set(self.missing)|getattr(self,'_history_pending_keys',set())
  try:
   # Implement projections without recreating generic system/execution containers.
   blocked=self.invalid|{c['key'] for c in self.conflicts}
   for key,r in self.latest.items():
    if not r or key in blocked:continue
    path=self.path(self.paths[key]);path.parent.mkdir(parents=True,exist_ok=True)
    for n in walk(r['data']):
     for f,h in [('fileKey','fileHash'),('photoKey','photoHash'),('logoKey','logoHash'),('signKey','signHash')]:
      rel=n.get(f);sha=n.get(h)
      if not rel:continue
      target=self.path(rel)
      if not target.exists() or sha and self.hash_file(target)!=sha:
       blob=self.blobs/str(sha)
       if sha and blob.is_file() and self.hash_file(blob)==sha:atomic(target,blob.read_bytes())
       else:self.warnings.append({'key':key,'path':rel,'message':'Ожидается файл выбранной версии. Проверьте синхронизацию.'})
    content=encode(r['data'])
    if not path.exists() or path.read_bytes()!=content:atomic(path,content)
    self.materialized[key]=list(self.heads[key]);self.known[key]={'files':[self.paths[key]]+[n[f] for n in walk(r['data']) for f in ('fileKey','photoKey','logoKey','signKey') if n.get(f)]}
    if r['kind']=='acts':
     for name in ('Схемы к акту','Испытания к акту','Фотографии'):(path.parent/name).mkdir(exist_ok=True)
   for key,r in self.latest.items():
    if r is None:self.known.pop(key,None)
   ledger=encode(self.known)
   if not self.ledger_path.exists() or self.ledger_path.read_bytes()!=ledger:atomic(self.ledger_path,ledger)
  finally:self.invalid=saved_invalid
  if getattr(self,'_history_pruned',set()):self._collect_history()
 def load(self):
  self.metrics['loads']+=1
  result=super().load()
  if result['state'] and result['state']['meta'].get('folderModel',0)<9 and not self._saving and not result['conflicts'] and not self.invalid and not self.missing:
   self._checkpoint('Перед переходом на структуру 0.9')
   return self.save(migrate(result['state']),self.revision)
  return result
 def _context(self,r,records):
  p=s=a=None;cur=r
  while cur:
   if cur['kind']=='projects':p=cur['data']
   if cur['kind']=='systems':s=cur['data']
   if cur['kind']=='acts':a=cur['data']
   cur=records.get(cur.get('parent'))
  return p,s,a
 def _file_name(self,r,node,trail,records,ext):
  p,s,a=self._context(r,records);kind=r['kind'];label=node.get('name') or node.get('cap') or node.get('type') or self._title(r)
  if trail and trail[0]=='scheme':prefix='Схема';label='Исполнительная схема'
  elif 'schemes' in trail:prefix='Схема'
  elif 'tests' in trail or kind=='trials':prefix='Испытание'
  elif 'photos' in trail:prefix='Фото'
  elif 'scan' in trail:prefix=a.get('type','АОСР') if a else 'Подписанный акт';label='Подписанный'
  elif 'frameTemplate' in trail:prefix='Шаблон рамки'
  elif kind in ('base','materials'):prefix=node.get('type','Документ качества');label=r['data'].get('name','Материал')+'_'+node.get('num','')+'_'+node.get('date','')
  elif kind=='templates':prefix='Шаблон';label=r['data'].get('name','Word')
  else:prefix=LABELS.get(kind,'Документ')
  parts=[prefix,s.get('code') if s else '',a.get('num') if a else '',label]
  value='_'.join(str(x) for x in parts if x);value=re.sub(r'[\s.\-]+','_',value);value=re.sub('_+','_',value).strip('_')
  return safe(value)[:130]+ext.lower()
 def _place(self,r,path):
  folder=self.path(path).parent;folder.mkdir(parents=True,exist_ok=True);records=self._records
  def process(node,trail=()):
   if isinstance(node,list):
    for i,x in enumerate(node):process(x,trail+(str(i),))
    return
   if not isinstance(node,dict):return
   for field in ('img','photo','logo','sign'):
    value=node.get(field)
    if isinstance(value,str) and value.startswith('data:image/'):
     import base64
     data=base64.b64decode(value.split(',',1)[1]);ext='.png' if 'image/png' in value[:30] else '.jpg';name=safe(node.get('cap') or 'Фото объекта' if field=='photo' else node.get('cap') or field)+ext
     tmp=self.files/uuid.uuid4().hex/name;atomic(tmp,data);node[field+'Key' if field!='img' else 'fileKey']=tmp.relative_to(self.root).as_posix();node[field+'Hash' if field!='img' else 'fileHash']=self._blob(tmp);node[field]=tmp.relative_to(self.root).as_posix()
   for f,h in [('fileKey','fileHash'),('photoKey','photoHash'),('logoKey','logoHash'),('signKey','signHash')]:
    rel=node.get(f)
    if not rel:continue
    source=self.path(rel);sha=node.get(h)
    if source.is_file():
     actual=self.hash_file(source)
     if not sha or source.is_relative_to(self.files) or actual==sha:sha=self._blob(source);node[h]=sha
    blob=self.blobs/str(sha)
    if not sha or not blob.is_file():raise ValueError('Не найден исходный документ: '+rel)
    # A library reference remains global; it must never create copies in projects.
    if r['kind']=='materials' and r['data'].get('baseId'):continue
    ext=Path(rel).suffix or '.pdf';name=self._file_name(r,node,trail,records,ext)
    section='Схемы к акту' if 'schemes' in trail else 'Испытания к акту' if 'tests' in trail else 'Фотографии' if 'photos' in trail else ''
    if r['kind']=='trash':target=source if source.is_relative_to(folder) else folder/'Документы'/Path(rel)
    else:target=folder/section/name
    occupied=self._occupied.setdefault(str(folder/section),{})
    token=(node.get('id') or '/'.join(trail),f)
    if target.name in occupied and occupied[target.name]!=token:target=target.with_name(target.stem+'_'+hashlib.sha256(str(token).encode()).hexdigest()[:4]+ext)
    occupied[target.name]=token
    if not target.exists() or self.hash_file(target)!=sha:atomic(target,blob.read_bytes())
    new=target.relative_to(self.root).as_posix();node[f]=new
    if f=='fileKey':node['file']=target.name
    if f=='photoKey':node['photo']=new
    if f=='logoKey':node['logo']=new
    if f=='signKey':node['sign']=new
    if node.get('img') and f=='fileKey':node['img']=new
   for k,v in list(node.items()):
    if isinstance(v,(dict,list)):process(v,trail+(k,))
  process(r['data'])
 def save(self,state,expected_revision,base_state=None,base_heads=None):
  self.metrics['saves']+=1
  if base_state is not None:
   self.baseline=__import__('folder_core').flatten(migrate(validate_state(base_state)))
   if base_heads is not None:self.base_heads=copy.deepcopy(base_heads)
  original_records=__import__('folder_core').flatten(validate_state(state))
  state=migrate(state)
  if not self.ready:self.load()
  before=copy.deepcopy(self.baseline);parents=copy.deepcopy(self.base_heads);self.ui=copy.deepcopy(state.get('ui',{}));records=__import__('folder_core').flatten(state);self._records=records;self._occupied={};self._scan();self._disk_changes();self._scan();blocked={c['key'] for c in self.conflicts}|getattr(self,'_history_pending_keys',set())
  oldpaths=copy.deepcopy(self.paths);paths={k:portable_path(self._record_path(k,r,records)) for k,r in records.items()}
  for key,r in records.items():
   if key in self.invalid and original_records.get(key)==before.get(key):r=records[key]=copy.deepcopy(before[key])
   if key in self.invalid or key in self.missing or key in blocked:
    if r!=before.get(key):raise ValueError('Сначала восстановите файл, JSON или разрешите конфликт: '+self.paths[key])
    paths[key]=self.paths[key];continue
   if r!=before.get(key) or paths[key]!=oldpaths.get(key):self._place(r,paths[key])
  self._saving=True
  try:
   changed=[]
   for key in set(before)|set(records):
    r=records.get(key);path=paths.get(key) or oldpaths[key]
    if r==before.get(key) and path==oldpaths.get(key):continue
    if key in blocked:raise ValueError('Карточка заблокирована до выбора версии конфликта: '+key)
    self._emit(key,r,parents.get(key,[]),path);changed.append(key)
   # Publish this save's own JSON projections before scanning them as external edits.
   # Unchanged, damaged and concurrent cards are deliberately left alone.
   self._scan();conflicted={c['key'] for c in self.conflicts}
   for key in changed:
    record=records.get(key)
    if record and key not in conflicted and key not in self.invalid and key not in self.missing and self.latest.get(key)==record:
     atomic(self.path(self.paths[key]),encode(record['data']))
   result=self.load()
   self._cleanup_projections(before,oldpaths)
   self._archive_previous()
   if not self.invalid and not self.conflicts and not self.warnings:self._checkpoint('Автоматически')
   return result
  finally:self._saving=False
 def _cleanup_projections(self,before,oldpaths):
  current={str(self.path(p)) for k,p in self.paths.items() if self.latest.get(k)}
  refs={str(self.path(n[f])) for r in self.latest.values() if r for n in walk(r['data']) for f in ('fileKey','photoKey','logoKey','signKey') if n.get(f)}
  for key,old in before.items():
   if not old or key not in oldpaths:continue
   oldpath=self.path(oldpaths[key]);active=self.latest.get(key)
   if str(oldpath) not in current and oldpath.is_file():oldpath.unlink()
   for n in walk(old['data']):
    for f in ('fileKey','photoKey','logoKey','signKey'):
     if n.get(f):
      p=self.path(n[f])
      if str(p) not in refs and p.is_file() and not p.is_relative_to(self.service):p.unlink()
  # Only examine paths belonging to changed/deleted projections, never the whole database.
  folders=set()
  for key,rel in oldpaths.items():
   if key not in self.paths or self.latest.get(key) is None or self.paths[key]!=rel:
    parent=self.path(rel).parent
    if self.latest.get(key) is None and (before.get(key) or {}).get('kind')=='trash' and parent.exists():
     if not any(Path(ref).is_relative_to(parent) for ref in refs):shutil.rmtree(parent);continue
    while parent!=self.root and not parent.is_relative_to(self.service):folders.add(parent);parent=parent.parent
  for folder in sorted(folders,key=lambda x:len(x.parts),reverse=True):
   # Empty generated attachment folders can be removed along with their act.
   if folder.exists():
    for child in list(folder.iterdir()):
     if child.is_dir():
      try:child.rmdir()
      except OSError:pass
    try:folder.rmdir()
    except OSError:pass
 def recover_missing(self,key):
  self._scan();path=self.paths.get(key)
  if not path:raise ValueError('Карточка не найдена')
  prefix=Path(path).parent.as_posix()+'/'
  keys=[k for k,p in self.paths.items() if k==key or Path(p).as_posix().startswith(prefix)]
  self.force.update(keys)
  try:return self.load()
  finally:self.force.difference_update(keys)
 def repair(self,key,data):
  self._scan();r=self.latest.get(key)
  if not r:raise ValueError('Карточка не найдена')
  self._validate_card(data,r);p=self.path(self.paths[key])
  if p.exists():atomic(self.service/'Повреждённые JSON'/(uuid.uuid4().hex[:8]+'_'+p.name),p.read_bytes())
  r=copy.deepcopy(r);r['data']=data;self._emit(key,r,self.heads[key],self.paths[key]);atomic(p,encode(data));return self.load()
 def _entity(self,state,ent,ident,pid=None):
  libs={'base':'base','org':'orgs','per':'people','ord':'orders','pf':'profiles','tpl':'templates'}
  if ent in libs:
   arr=state['lib'][libs[ent]];o=next((x for x in arr if x['id']==ident),None);return arr,o,{}
  for p in state['projects']:
   if pid and p['id']!=pid:continue
   if ent=='proj' and p['id']==ident:return state['projects'],p,{'pid':p['id']}
   for field,typ in [('executions','exec'),('systems','sys'),('materials','mat'),('journals','jr')]:
    for o in p.get(field,[]):
     if ent==typ and o['id']==ident:return p[field],o,{'pid':p['id'],'eid':o.get('executionId',o['id'] if typ=='exec' else ''),'sid':o['id'] if typ=='sys' else ''}
   for s in p['systems']:
    for field,typ in [('acts','act'),('aik','aik'),('journals','jr')]:
     for o in s.get(field,[]):
      if ent==typ and o['id']==ident:return s[field],o,{'pid':p['id'],'sid':s['id'],'eid':s.get('executionId','')}
  return None,None,{}
 @staticmethod
 def _nested(obj,path):
  for part in path.split('.') if path else []:
   obj=next((x for x in obj if x.get('id')==part[1:]),None) if part.startswith('#') else obj.get(part)
   if obj is None:raise ValueError('Карточка или список больше не существует')
  return obj
 def move_trash(self,params):
  result=self.load() if not params.get('preview') else {'state':copy.deepcopy(params['state'])};state=result['state']
  if not state:raise ValueError('База пуста')
  arr,obj,ctx=self._entity(state,params['ent'],params['id'],params.get('pid'))
  if obj is None:raise ValueError('Элемент не найден')
  ent=params['ent'];item=copy.deepcopy(obj)
  if params.get('row'):
   owner=obj;arr=self._nested(owner,params['path']);item=next((x for x in arr if x['id']==params['row']),None)
   if item is None:raise ValueError('Документ не найден')
   ctx.update(parentEnt=ent,parentId=obj['id'],path=params['path']);ent='row'
  elif ent=='exec':
   p=next(p for p in state['projects'] if p['id']==ctx['pid']);item={'execution':item,'systems':[s for s in p['systems'] if s.get('executionId')==obj['id']]};p['systems']=[s for s in p['systems'] if s.get('executionId')!=obj['id']]
  project=next((p for p in state['projects'] if p['id']==ctx.get('pid')),None)
  exe=next((e for e in (project or {}).get('executions',[]) if e['id']==ctx.get('eid')),None)
  where=' / '.join(x for x in ((project or {}).get('short') or (project or {}).get('name'),(exe or {}).get('name'),obj.get('code') if params['ent']=='sys' else None) if x) or 'Справочник'
  name=(item.get('execution') or item).get('name') or item.get('num') or item.get('file') or 'Документ'
  arr.remove(obj if ent!='row' else item)
  ident='trash-'+uuid.uuid4().hex
  state.setdefault('trash',[]).insert(0,{'id':ident,'ent':ent,'item':item,'ctx':ctx,'name':name,'where':where,'ts':stamp(),'by':params.get('user') or self.actor})
  state.setdefault('history',[]).insert(0,{'id':uuid.uuid4().hex,'ts':stamp(),'user':params.get('user') or self.actor,'text':'Перемещено в корзину: '+name})
  return self._edit_result(state,params)
 def _edit_result(self,state,params):
  if params.get('preview'):return {'state':migrate(validate_state(state)),'revision':self.revision,'root':str(self.root),'preview':True,'warnings':self.warnings,'conflicts':self.conflicts}
  return self.save(state,self.revision)
 def _restore_item(self,state,tid,params):
  t=next((x for x in state['trash'] if x['id']==tid),None)
  if not t:raise ValueError('Элемент корзины не найден')
  ent=t['ent'];ctx=t.get('ctx',{});item=copy.deepcopy(t['item']);pid=params.get('targetProject') or ctx.get('pid');eid=params.get('targetExecution') or ctx.get('eid');sid=params.get('targetSystem') or ctx.get('sid')
  p=next((p for p in state['projects'] if p['id']==pid),None)
  if not p and pid and ent!='proj':
   parent=next((x for x in state['trash'] if x['ent']=='proj' and x['item']['id']==pid),None)
   if parent and params.get('restoreParents'):self._restore_item(state,parent['id'],params);p=next(p for p in state['projects'] if p['id']==pid)
   else:raise ValueError('Объект удалён. Восстановите его либо выберите другой объект.')
  if ent=='sys' and not any(e['id']==eid for e in p['executions']):
   parent=next((x for x in state['trash'] if x['ent']=='exec' and x['item']['execution']['id']==eid),None)
   if parent and params.get('restoreParents'):self._restore_item(state,parent['id'],params)
   else:raise ValueError('Выполнение удалено. Восстановите его либо выберите другое выполнение.')
  if ent=='proj':arr=state['projects']
  elif ent=='exec':arr=p['executions'];execution=item['execution'];systems=item['systems'];item=execution
  elif ent=='sys':
   arr=p['systems'];item['executionId']=eid
   for a in item.get('acts',[]):a['executionId']=eid
  elif ent=='mat':arr=p['materials']
  elif ent in ('act','aik','jr'):
   system=next((s for s in p['systems'] if s['id']==sid),None)
   if ent=='jr' and not sid:arr=p['journals']
   else:
    if system is None:
     parent=next((x for x in state['trash'] if x['ent']=='sys' and x['item']['id']==sid),None)
     if parent and params.get('restoreParents'):self._restore_item(state,parent['id'],params);system=next(s for s in p['systems'] if s['id']==sid)
     else:raise ValueError('Система удалена. Восстановите её либо выберите другую систему.')
    arr=system[{'act':'acts','aik':'aik','jr':'journals'}[ent]]
    if ent=='act':item['executionId']=system['executionId']
  elif ent=='row':
   _,owner,_=self._entity(state,ctx['parentEnt'],ctx['parentId'])
   if owner is None:
    parent=next((x for x in state['trash'] if x['ent']==ctx['parentEnt'] and x['item'].get('id')==ctx['parentId']),None)
    if parent and params.get('restoreParents'):
     self._restore_item(state,parent['id'],params);_,owner,_=self._entity(state,ctx['parentEnt'],ctx['parentId'])
    if owner is None:raise ValueError('Родительская карточка удалена. Сначала восстановите её.')
   arr=self._nested(owner,ctx['path'])
  else:arr=state['lib'][{'base':'base','org':'orgs','per':'people','ord':'orders','pf':'profiles','tpl':'templates'}[ent]]
  if any(x.get('id')==item.get('id') for x in arr):raise ValueError('Эта карточка уже восстановлена. Существующие данные не перезаписаны.')
  label=item.get('name') or item.get('num')
  if label and any((ent!='sys' or x.get('executionId')==eid) and ((x.get('name') or x.get('num'))==label or ent=='sys' and x.get('code')==item.get('code')) for x in arr):
   field='name' if 'name' in item else 'num';item[field]=label+' — восстановлено'
  arr.append(item)
  if ent=='exec':p['systems'].extend(systems)
  state['trash'].remove(t)
 def restore_trash(self,params):
  state=copy.deepcopy(params['state']) if params.get('preview') else self.load()['state'];self._restore_item(state,params['id'],params)
  return self._edit_result(state,params)
 def _protected(self,state,t):
  bid=t['item'].get('id') if t['ent']=='base' else t.get('ctx',{}).get('parentId') if t['ent']=='row' and t.get('ctx',{}).get('parentEnt')=='base' else None
  sources=state['projects']+[x['item'] for x in state['trash'] if x['id']!=t['id']]
  if t['ent']=='row' and t.get('ctx',{}).get('parentEnt')=='mat' and t['ctx'].get('path')=='docs':
   mid=t['ctx']['parentId']
   if any(n.get('id')==mid for source in sources for n in walk(source)):return True
  if bid and any(n.get('baseId')==bid for source in sources for n in walk(source)):return True
  ident=t['item'].get('id')
  if not ident:return False
  def strings(x):
   if isinstance(x,str):yield x
   elif isinstance(x,dict):
    for k,v in x.items():
     if k!='id':yield from strings(v)
   elif isinstance(x,list):
    for v in x:yield from strings(v)
  needed=set(v for source in sources for v in strings(source))
  for _ in range(10):
   old=len(needed)
   for field,records in state['lib'].items():
    if isinstance(records,list):
     for record in records:
      if isinstance(record,dict) and record.get('id') in needed:needed.update(strings(record))
   if len(needed)==old:break
  return ident in needed
 def purge_trash(self,params):
  state=copy.deepcopy(params['state']) if params.get('preview') else self.load()['state'];selected=[t for t in state['trash'] if params.get('all') or t['id']==params.get('id')]
  check_state=copy.deepcopy(state);check_state['trash']=[t for t in state['trash'] if t not in selected]
  if any(self._protected(check_state,t) for t in selected):raise ValueError('Элемент используется в объектах. Удалите связи перед окончательным удалением.')
  folders=[self.path(self.paths['trash:'+t['id']]).parent for t in selected if 'trash:'+t['id'] in self.paths]
  state['trash']=[t for t in state['trash'] if t not in selected]
  if params.get('preview'):return self._edit_result(state,params)
  result=self.save(state,self.revision)
  for folder in folders:
   if folder.exists():shutil.rmtree(folder)
  return result
 def portable_export(self,state,target):
  """A selected, independently openable folder repository, with all used references."""
  import tempfile
  state=copy.deepcopy(validate_state(state));state['history']=[];state['builds']=[];state['locks']={};state['ui']={}
  def strings(v):
   if isinstance(v,str):yield v
   elif isinstance(v,dict):
    for x in v.values():yield from strings(x)
   elif isinstance(v,list):
    for x in v:yield from strings(x)
  needed=set(strings(state['projects']));lib={k:[] for k in ('base','quality','orgs','people','orders','profiles','templates')};chosen=set()
  original=state['lib'];all_trash=state.get('trash',[]);archived=[];project_ids={p['id'] for p in state['projects']}
  for _ in range(10):
   count=len(archived)
   for t in all_trash:
    if t in archived:continue
    ent=t.get('ent');ctx=t.get('ctx',{})
    usable=ent in ('base','mat') and t['item'].get('id') in needed or ent=='row' and ctx.get('parentEnt') in ('base','mat') and ctx.get('parentId') in needed
    if usable and (ent!='mat' or ctx.get('pid') in project_ids):archived.append(t);needed.update(strings(t['item']))
   if len(archived)==count:break
  state['trash']=archived
  for _ in range(10):
   changed=False
   for field in lib:
    for record in original.get(field,[]):
     if record['id'] in needed and (field,record['id']) not in chosen:
      chosen.add((field,record['id']));lib[field].append(record);needed.update(strings(record));changed=True
   if not changed:break
  people={p['id'] for p in lib['people']};lib['signMatrix']={k:[x for x in vals if x in people] for k,vals in original.get('signMatrix',{}).items()};state['lib']=lib
  target=Path(target).resolve()
  if target.is_relative_to(self.root):raise ValueError('Сохраните ZIP вне рабочей папки базы')
  with tempfile.TemporaryDirectory(prefix='sid-portable-') as temp:
   root=Path(temp)/'СтройИД';dest=Store(root);mapping={}
   for node in walk(state):
    for f,h in [('fileKey','fileHash'),('photoKey','photoHash'),('logoKey','logoHash'),('signKey','signHash')]:
     rel=node.get(f)
     if not rel:continue
     if rel not in mapping:
      src,_=self.asset_path(rel);mapping[rel]=dest.import_file(src)['id']
     node[f]=mapping[rel];node.pop(h,None)
     if node.get('img')==rel:node['img']=mapping[rel]
     for textfield in ('photo','logo','sign'):
      if node.get(textfield)==rel:node[textfield]=mapping[rel]
   dest.save(state,0);dest.close()
   with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for file in root.rglob('*'):
     if file.is_file() and not file.is_relative_to(dest.files):z.write(file,'СтройИД/'+file.relative_to(root).as_posix())
    z.writestr('Открыть комплект.txt','Распакуйте ZIP. В СтройИД выберите папку «СтройИД» как папку базы. Все файлы и необходимые справочники включены.\n'.encode('utf-8-sig'))
  return {'path':str(target),'projects':len(state['projects'])}
