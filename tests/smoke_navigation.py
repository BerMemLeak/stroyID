"""Back navigation preserves drafts; drawing refresh ignores outdated replies."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from pypdf import PdfWriter
from app import Window,dispose_window
from storage import Store
app=QApplication([]);temp=tempfile.TemporaryDirectory();root=Path(temp.name);store=Store(root/'data')
w=PdfWriter();w.add_blank_page(1191,842);w.add_blank_page(1191,842);w.write(root/'source.pdf');asset=store.import_file(root/'source.pdf')
window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(msg):errors.append(str(msg));app.exit(1)
def ready(value):
 global stage
 if not value or stage:return
 stage=1
 script=r'''(async()=>{try{
 const assert=(x,m)=>{if(!x)throw Error(m);},wait=ms=>new Promise(r=>setTimeout(r,ms));
 const until=async predicate=>{for(let i=0;i<300;i++){if(predicate())return;await wait(10);}throw Error('UI wait timed out');};
 S=seed();S.projects=S.projects.slice(0,1);S.locks={};IX=null;ensureWorkspace();
 const p=S.projects[0],s=p.systems[0],a=s.acts[0];Object.assign(s.scheme,{file:'source.pdf',fileKey:ASSET,pages:2,frameEnabled:true,num:'ИС-1'});
 await desktopFlush(true);
 history.replaceState(null,'','#/home');manualAcceptedHash=location.hash;navigationEntries=['#/home'];navigationIndex=0;render();
 assert(document.querySelector('[data-a="navigationBack"]').disabled,'Root back button must be disabled');
 const visit=async h=>{go(h);await until(()=>location.hash===h);await wait(30);assert(document.querySelector('#content [data-a="navigationBack"]'),'Missing back button '+h);};
 for(const h of ['#/lib/base','#/lib/orgs','#/lib/profiles','#/build/'+p.id,'#/p/'+p.id,'#/s/'+s.id+'/acts','#/a/'+a.id])await visit(h);
 const input=document.querySelector('[data-ent="act"][data-f="works"]');input.value='Работы сохраняются при возврате';input.dispatchEvent(new Event('input',{bubbles:true}));
 const native=nativeCall;let failSave=true;const pending=[];
 nativeCall=async(op,params)=>{
  if(op==='save'&&failSave)throw Error('test-save-failed');
  if(op==='previewDrawing')return new Promise(resolve=>pending.push({params,resolve}));
  return native(op,params);
 };
 await A.navigationBack();assert(location.hash==='#/a/'+a.id,'Failed save navigated away');assert(a.works===input.value,'Failed save lost input');closeModal();
 failSave=false;await A.navigationBack();await until(()=>location.hash==='#/s/'+s.id+'/acts');
 const saved=await native('load');assert(saved.state.projects[0].systems[0].acts[0].works==='Работы сохраняются при возврате','Back did not save draft');
 await visit('#/s/'+s.id+'/scheme');
 assert(document.querySelector('#content #drawing-result'),'Background drawing panel missing');
 const preview=A.drawingPreview;A.drawingPreview=()=>{};A.drawingEdit({s:s.id,x:'system'});A.drawingPreview=preview;
 const dialog=document.querySelector('.dlg'),q=selector=>dialog.querySelector(selector);
 assert(q('[data-a="drawingPreview"]').textContent.includes('Обновить'),'Refresh button missing');
 const d={s:s.id,x:'system'},one=A.drawingPreview(d);await until(()=>pending.length===1);
 const number=q('[data-frame-field="num"]');number.value='ИС-2';number.dispatchEvent(new Event('change',{bubbles:true}));
 assert(q('#drawing-preview-status').textContent.includes('изменены'),'Change did not mark preview stale');
 const two=A.drawingPreview(d);await until(()=>pending.length===2);
 assert(pending[1].params.frame.values['Схема.Номер']==='ИС-2','Refresh used old metadata');
 const image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jf9sAAAAASUVORK5CYII=';
 pending[1].resolve({width:420,height:297,pages:2,image:image+'#new'});await two;
 pending[0].resolve({width:420,height:297,pages:2,image:image+'#old'});await one;
 assert(q('.frame-preview').getAttribute('src').endsWith('#new'),'Old reply overwrote new preview');
 const page=q('#drawing-page');page.value='2';page.dispatchEvent(new Event('input',{bubbles:true}));
 const three=A.drawingPreview(d);await until(()=>pending.length===3);assert(pending[2].params.page===2,'Refresh ignored selected page');
 pending[2].resolve({width:420,height:297,pages:2,image:image+'#page2'});await three;
 assert(q('#drawing-preview-status').textContent==='Предпросмотр обновлён.','Refresh success not shown');
 assert(!document.querySelector('#content .frame-preview'),'Modal refresh changed background preview');
 closeModal();nativeCall=native;
 history.replaceState(null,'','#/a/'+a.id);manualAcceptedHash=location.hash;navigationEntries=[location.hash];navigationIndex=0;render();
 await A.navigationBack();await until(()=>location.hash==='#/s/'+s.id+'/acts');
 await A.navigationBack();await until(()=>location.hash==='#/p/'+p.id);
 assert(!document.querySelector('.dlg'),'Back opened an unexpected dialog');
 window.navigationResult=JSON.stringify({ok:true});
 }catch(e){window.navigationResult=JSON.stringify({ok:false,error:e.stack});}})();'''.replace('ASSET',json.dumps(asset['id']))
 window.page.runJavaScript(script)
def finish(value):
 global stage
 if not value:return
 try:
  result=json.loads(value);assert result['ok'],result;assert not window.page.console_errors,window.page.console_errors
  print('PASS: back on pages, save failure/retry, deep-link parents, preview refresh and stale reply isolation');stage=2;app.exit()
 except Exception as exc:fail(exc)
def tick():
 if stage==0:window.page.runJavaScript('window.desktopReady===true',ready)
 elif stage==1:window.page.runJavaScript('window.navigationResult||null',finish)
timer=QTimer();timer.timeout.connect(tick);timer.start(100);QTimer.singleShot(90000,lambda:fail('Navigation smoke timed out'))
code=app.exec();dispose_window(window);store.close();temp.cleanup()
if errors:print('\n'.join(errors),file=sys.stderr)
sys.exit(1 if errors or stage!=2 else code)
