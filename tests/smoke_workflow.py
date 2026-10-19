"""Real WebEngine regression coverage for shared certificates and automatic saving."""
import json, sys, tempfile, traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from pypdf import PdfWriter
from app import Window, dispose_window
from folder_store import Store
app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);store=Store(root/'db')
w=PdfWriter();w.add_blank_page(595,842);w.write(root/'certificate.pdf')
window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(e): errors.append(str(e));app.exit(1)
def ready(value):
 global stage
 if not value or stage:return
 stage=1
 script=r'''(async()=>{try{
 const assert=(v,m)=>{if(!v)throw Error(m);},delay=ms=>new Promise(r=>setTimeout(r,ms));
 const waitFor=async(fn,message)=>{const end=Date.now()+10000;while(!fn()){if(desktopError)throw Error(desktopError);if(Date.now()>end)throw Error(message);await delay(50);}};
 S=seed();S.projects=S.projects.slice(0,1);S.lib.base=[];S.lib.quality=[];S.trash=[];S.locks={};ensureWorkspace();
 const p=S.projects[0],s=p.systems[0],a=s.acts[0];p.materials=[{id:'mat-a',name:'Труба 20',category:'Трубы',maker:'Завод',docs:[],baseId:''},{id:'mat-b',name:'Труба 40',category:'Трубы',maker:'Завод',docs:[],baseId:''},{id:'mat-c',name:'Кабель',category:'Кабели',docs:[],baseId:''}];
 a.materials=['mat-a'];a.aikLinks={};s.materialIds=[];save();await desktopFlush();
 A.qualityEdit({ent:'mat',id:'mat-a'});document.querySelector('#quality-num').value='CERT-77';document.querySelector('#quality-from').value='2026-01-01';document.querySelector('#quality-to').value='2027-01-01';await A.qualityFile();document.querySelector('.dlg [value="mat-b"]').checked=true;MB[1].f();closeModal();await desktopFlush();
 assert(S.lib.quality.length===1,'Expected one certificate');const q=S.lib.quality[0];assert(mDocs(p.materials[0])[0]===q&&mDocs(p.materials[1])[0]===q,'Materials must resolve the same record');assert(p.materials.every(m=>!m.docs.length),'Shared file copied to materials');
 A.qualityEdit({ent:'mat',id:'mat-b',q:q.id});document.querySelector('#quality-num').value='CERT-UPDATED';MB[1].f();closeModal();await desktopFlush();assert(mDocs(p.materials[0])[0].num==='CERT-UPDATED','Shared edit not propagated');
 A.qualityUnlink({ent:'mat',id:'mat-a',q:q.id});await desktopFlush();assert(mDocs(p.materials[0]).length===0&&mDocs(p.materials[1]).length===1,'Unlink damaged another material');
 A.qualityChoose({ent:'mat',id:'mat-a'});document.querySelector('.dlg [value="'+q.id+'"]').checked=true;MB[1].f();closeModal();await desktopFlush();
 const loaded=await nativeCall('load');assert(loaded.state.lib.quality.length===1&&loaded.state.projects[0].materials[0].docIds[0]===q.id,'Shared references lost after persistence');
 A.actMatAdd({id:a.id});const search=document.querySelector('[data-material-search]');search.value='CERT-UPDATED';search.dispatchEvent(new Event('input',{bubbles:true}));assert(document.querySelectorAll('[data-material-row]:not([hidden])').length===2,'Search by shared certificate');A.materialSelectVisible();MB[1].f();closeModal();assert(a.materials.length===2,'Multiple material selection');
 A.systemMatPick({s:s.id});const cat=document.querySelector('[data-material-category]');cat.value='Кабели';cat.dispatchEvent(new Event('change',{bubbles:true}));A.materialSelectVisible();MB[1].f();closeModal();assert(s.materialIds.join()==='mat-c','Category filter and multi select');
 history.replaceState(null,'','#/a/'+a.id);manualAcceptedHash=location.hash;render();const field=document.querySelector('[data-ent="act"][data-f="works"]');field.value='Автоматически сохранённые работы';field.dispatchEvent(new Event('input',{bubbles:true}));await waitFor(()=>!desktopDirty&&!desktopSaving,'Debounced save did not finish');assert((await nativeCall('load')).state.projects[0].systems[0].acts[0].works===field.value,'Auto-save missing on disk');
 field.value='Сохранение перед переходом';field.dispatchEvent(new Event('input',{bubbles:true}));go('#/lib/base');await waitFor(()=>location.hash==='#/lib/base','Saved navigation did not finish');assert(location.hash==='#/lib/base'&&!document.querySelector('.dlg'),'Navigation prompts despite auto-save');
 const before=s.sketches.length;A.sketchAdd({s:s.id});closeModal();await delay(900);assert(s.sketches.length===before,'Cancelled scheme created phantom');A.sketchAdd({s:s.id});await A.schemeDraftFile();MB[1].f();closeModal();await desktopFlush();assert(s.sketches.length===before+1&&s.sketches.at(-1).fileKey,'Valid scheme not created');
 const owned={...ROWT.scheme(a),id:'owned-test',file:'certificate.pdf',fileKey:q.fileKey,pages:1};a.schemes.push(owned);ensureWorkspace();const item=resourceList(s).find(x=>x.id===owned.id);assert(schemeActs(s,item).some(x=>x.id===a.id),'Owning act missing from scheme links');assert(owned.frameEnabled===true,'Frame not enabled by default');
 A.executionEdit({p:p.id,e:p.executions[0].id});document.querySelector('#execution-start').value='2026-01-01';document.querySelector('#execution-end').value='2026-02-01';MB[1].f();closeModal();await desktopFlush();assert(p.executions[0].end==='2026-02-01','Execution end lost');
 const pf=S.lib.profiles[0];pf.exportSettings={order:EXPORT_BLOCKS.map(x=>x[0]),off:[]};p.exportMode='custom';history.replaceState(null,'','#/lib/profiles/'+pf.id);manualAcceptedHash=location.hash;render();let rows=[...document.querySelectorAll('[data-sort-action="profileMove"]')];assert(rows.length===EXPORT_BLOCKS.length,'Drag handles missing');reorderExport(rows[0],rows[2]);assert(pf.exportSettings.order[2]==='title','Drag did not reorder');
 history.replaceState(null,'','#/build/'+p.id);manualAcceptedHash=location.hash;render();assert(document.querySelector('[data-assembly="includeCommon"]')&&document.querySelector('[data-assembly="includeOperations"]'),'Explicit export switches missing');
 const common=document.querySelector('[data-assembly="includeCommon"]');common.checked=false;common.dispatchEvent(new Event('change',{bubbles:true}));assert(assemblyRules(p,{volumes:[{kind:'T1',documents:[]},{kind:'T2',documents:[]},{kind:'T3',documents:[]}]}).volumes.every(v=>v.kind!=='T1'),'Common switch ignored');
 const company={id:'issuer-test',full:'ООО Выпускающая компания',short:'Выпускающая',logo:''};S.lib.orgs.push(company);p.exportIssuer=company.id;const original=p.genContractor,context=wordContext(p,volumeList(p).find(v=>v.s?.id===s.id),'title');assert(context.values.Генподрядчик===company.full&&p.genContractor===original,'Export company mutates object');
 history.replaceState(null,'','#/p/'+p.id+'/general');render();assert(document.querySelector('a[href="#/p/'+p.id+'/additional"]'),'Additional documents card missing');history.replaceState(null,'','#/s/'+s.id+'/schemes');render();assert(!document.querySelector('.ph [data-a="newAct"]')&&!document.querySelector('.ph [data-ent="sys"][data-a="del"]'),'Redundant system header buttons');
 S.ui.wordObject=p.id;S.ui.wordProfile='';history.replaceState(null,'','#/lib/templates');render();assert(!document.querySelector('[data-word-section="orders"]')&&!document.querySelector('[data-word-section="quality"]')&&!document.querySelector('[data-word-section="pass"]'),'Removed template sections still visible');assert(document.querySelector('[data-a="frameProfilePick"]'),'HTML frame upload missing');
 const duplicateQuality={id:'q-shared_act',qualityId:'q-shared',qualityMode:'each'};assert(assemblyRules(p,{volumes:[{kind:'T2',documents:[{...duplicateQuality},{...duplicateQuality}]}]}).volumes[0].documents.length===1,'Certificate repeated for materials within one act');
 assert(shortFio('  Иванов   Иван Иванович  ')==='Иванов И. И.','FIO initials');
 await desktopFlush();window.workflowResult={ok:true,quality:q.id,pid:p.id};
 }catch(e){window.workflowResult={error:e.stack};}})();'''
 window.page.runJavaScript(script)
def receive(value):
 global stage
 if stage!=1 or not value:return
 result=json.loads(value)
 if result.get('error'):fail(result['error']);return
 try:
  assert not window.page.console_errors,window.page.console_errors
  state=store.load()['state'];q=state['lib']['quality'][0];assert len(state['lib']['quality'])==1
  assert store.asset_path(q['fileKey'])[0].is_file();assert not list((store.root/state['projects'][0]['name']).glob('**/Материалы/**/*.pdf'))
  screenshot=Path('validation/workflow-ui.png');screenshot.parent.mkdir(exist_ok=True);window.grab().save(str(screenshot.resolve()))
  stage=2;timer.stop();print('PASS: shared certificate create/edit/unlink/reload, filtered multi-selection, auto-save/navigation, cancelled scheme, owned scheme links, execution dates, drag ordering, export controls/company isolation, HTML templates and FIO');window.close()
 except Exception:fail(traceback.format_exc())
def poll():
 if stage==0:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.workflowResult?JSON.stringify(window.workflowResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Workflow timed out'))
with patch('app.QFileDialog.getOpenFileName',return_value=(str(root/'certificate.pdf'),'PDF')):code=app.exec()
dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
