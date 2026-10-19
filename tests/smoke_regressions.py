"""Repeat reported local workflows; --workspace tests a disposable copy of a real database."""
import sys,json,tempfile,shutil,traceback,io
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from pypdf import PdfWriter
from app import Window,dispose_window
from folder_store import Store
from pdf_export import prepare_export,write_export,ExportSourceError
app=QApplication([]);temp=tempfile.TemporaryDirectory();root=Path(temp.name)
if '--workspace' in sys.argv:
 source=Path(sys.argv[sys.argv.index('--workspace')+1]);shutil.copytree(source,root/'base')
store=Store(root/'base');window=Window(store,test_profile=True);window.setMinimumSize(500,600);window.resize(1024,850);window.show();stage=0;errors=[];widths=iter([800,1024,1280,1920]);measured=[]
pdf=root/'Проверочный документ.pdf';writer=PdfWriter();writer.add_blank_page(600,800);writer.write(pdf)
def fail(e):errors.append(str(e));app.exit(1)
def started(v):
 global stage
 if stage or not v:return
 stage=1
 window.page.runJavaScript('''(async()=>{try{
 window.regressionSynthetic=!S.projects.length;
 if(!S.projects.length){A.newProject();document.querySelector('#np-n').value='Проверочный объект';document.querySelector('[data-mb="1"]').click();await desktopFlush(true);A.newSystem({p:S.projects[0].id});document.querySelector('input[name=ns][value="ВК"]').checked=true;document.querySelector('[data-mb="1"]').click();await desktopFlush(true);A.newAct({s:S.projects[0].systems[0].id});document.querySelector('[data-mb="1"]').click();await desktopFlush(true);}
 const p=S.projects[0];window.regressionPid=p.id;window.regressionSid=p.systems[0].id;
 // The isolated export fixture includes a real, filled quantity statement.
 // A supplied workspace retains its own act data and validation results.
 if(window.regressionSynthetic){
  const a=p.systems[0].acts[0];a.works='Монтаж трубопроводов';
  a.quantityRows=[{id:'reg-quantity-1',name:'Монтаж трубы',place:'Этаж 1',unit:'м',qty:'12,5'},
   {id:'reg-quantity-2',name:'Установка креплений',place:'Этаж 1',unit:'шт.',qty:'8'}];
  save();await desktopFlush(true);
 }
 // Reordered identified rows must never alias or mutate one another.
 const first={id:'A',x:1},second={id:'B',x:2},rows=[first,second];reconcile(rows,[{id:'B',x:3},{id:'C',x:4}]);
 if(rows[0]!==second||rows[0]===rows[1]||rows[0].id!=='B'||rows[1].id!=='C'||first.id!=='A')throw Error('Identified-array corruption');
 const start=p.admin.length;A.objectDocAdd({p:p.id,key:'admin'});if(p.admin.length!==start)throw Error('New document persisted before Add');
 document.querySelector('[data-mb="1"]').click();if(p.admin.length!==start)throw Error('Blank document accepted');closeModal();await nativeCall('load');
 const originalIds=S.lib.people.map(x=>x.id),org=S.lib.orgs[0]?.id||'';
 for(let n=0;n<5;n++){S.lib.people.push({id:'reg-person-'+(5-n),fio:'Представитель '+n,fioShort:'Одинаковое название',position:'Инженер',orgId:org,docRole:1,authority:'',nrs:'',sign:''});save();await desktopFlush(true);if(folderWarnings.length||folderConflicts.length)throw Error(JSON.stringify(folderWarnings));await A.folderRefresh();}
 for(let pass=0;pass<8;pass++){
  for(const h of ['#/lib/base','#/lib/people','#/p/'+p.id+'/mats','#/s/'+p.systems[0].id+'/subs']){
   history.replaceState(null,'',h);manualAcceptedHash=h;render();if(document.querySelector('#content').innerText.includes('Ошибка отображения'))throw Error(h);
  }await A.folderRefresh();if(!S.ui.f||!S.ui.sel)throw Error('UI preferences disappeared');
 }
 S.ui.f.bq='проверка фильтра';save();await desktopFlush(true);await A.folderRefresh();if(S.ui.f.bq!=='проверка фильтра')throw Error('Filter reset');
 S.lib.people=S.lib.people.filter(x=>originalIds.includes(x.id));save();await desktopFlush(true);
 const draftCount=p.admin.length;A.objectDocAdd({p:p.id,key:'admin'});await A.commonDraftFile();if(p.admin.length!==draftCount)throw Error('PDF chooser committed draft');document.querySelector('#common-doc-name').value='Добавленный проверочный PDF';document.querySelector('[data-mb="1"]').click();await desktopFlush(true);
 if(p.admin.length!==draftCount+1||!p.admin.at(-1).fileKey)throw Error('Explicit document creation lost attachment');
 // A plan built from the actual workspace must name and link the empty source.
 const plan=pdfPlan(p,volumeList(p));window.regressionPlan=plan;
 if(plan.volumes.some(v=>v.documents.some(d=>d.kind==='pdf'&&!d.key))){const error=await nativeCall('exportPdf',{plan}).catch(e=>e);if(!error.details?.some(x=>x.ref&&x.cardPath)||!exportIssueLinks(error.details).includes('exportIssueOpen'))throw Error('Native export error lost source details');}

 history.replaceState(null,'','#/s/'+p.systems[0].id);manualAcceptedHash=location.hash;render();window.regressionResult={ok:true,plan};
 }catch(e){window.regressionResult={error:e.stack};}})();''')
def receive(raw):
 global stage
 if not raw or raw=='null':return
 value=json.loads(raw)
 if value.get('error'):fail(value['error']);return
 if stage!=1:return
 stage=2
 try:
  plan=value['plan'];missing=[d for v in plan['volumes'] for d in v['documents'] if d['kind']=='pdf' and not d.get('key')]
  if '--workspace' in sys.argv:
   assert len(missing)==1,missing;doc=missing[0];assert 'Новый документ' in doc['sourceLocation'] and doc['sourceRef'].endswith('/admin')
   try:prepare_export(store,plan)
   except ExportSourceError as ex:
    assert ex.details[0]['cardPath'].endswith('Новый документ/Карточка.json');assert ex.details[0]['ref']==doc['sourceRef'];print('PASS exact missing-source location and card route:',ex.details[0]['location'])
   else:raise AssertionError('Empty source silently skipped')
  # Explicit test selection: exclude ONLY the diagnosed empty card in memory.
  # Production data and the uploaded ZIP remain unchanged. Use builtin forms to
  # check actual source PDFs here; genuine Word launch is covered separately.
  # Keep document IDs so act references still resolve to quantity attachments.
  for volume in plan['volumes']:
   volume['documents']=[d for d in volume['documents'] if d not in missing]
   for d in volume['documents']:
    if d['kind']=='word':d.update(kind='html',html='<h1>Проверка комплекта</h1>')
    if d['kind']=='registry':d.pop('templateKey',None)
  built=prepare_export(store,plan);result=write_export(built,root/'Проверенный комплект.pdf',store);assert result['pages']>4
  assert not store.load()['warnings'];print('PASS repeated local creation/save/refresh, passports/signers, cancelled and completed document drafts; PDF:',result['pages'],'pages')
  next_width()
 except Exception:fail(traceback.format_exc())
def next_width():
 try:width=next(widths)
 except StopIteration:
  print('PASS responsive system menu at widths',measured)
  if window.page.console_errors:fail(window.page.console_errors)
  else:app.exit(0)
  return
 window.resize(width,850);QTimer.singleShot(250,lambda:window.page.runJavaScript('''(()=>{render();const menu=document.querySelector('.system-tabs');return JSON.stringify({width:innerWidth,okay:!!menu&&menu.scrollWidth<=menu.clientWidth+1&&[...menu.children].every(x=>x.getBoundingClientRect().right<=menu.getBoundingClientRect().right+1)})})()''',check_width))
def check_width(v):
 if isinstance(v,str) and v:v=json.loads(v)
 if not v or not v['okay']:fail('Menu overflows: '+repr(v)+'; console='+str(window.page.console_errors));return
 measured.append(v['width']);next_width()
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady',started)
 elif stage==1:window.page.runJavaScript('window.regressionResult?JSON.stringify(window.regressionResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(150);QTimer.singleShot(90000,lambda:fail('regression timeout'))
with patch('app.QFileDialog.getOpenFileName',return_value=(str(pdf),'PDF')):code=app.exec()
timer.stop();dispose_window(window);store.close()
if code==0:
 reopened=Store(root/'base');r=reopened.load();assert not r['warnings'],r['warnings'];assert not r['conflicts'];assert not any(x['id'].startswith('reg-person-') for x in r['state']['lib']['people']);reopened.close();print('PASS reopen after all operations, no corrupt cards')
temp.cleanup();print('\n'.join(errors));sys.exit(1 if errors else code)
