"""Real WebEngine coverage for frame metadata, shared drawings and export warnings."""
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
w=PdfWriter();[w.add_blank_page(1191,842) for _ in range(3)];w.write(root/'certificate.pdf');asset=store.import_file(root/'certificate.pdf')
window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(e): errors.append(str(e));app.exit(1)
def ready(value):
 global stage
 if not value or stage:return
 stage=1
 script=r'''(async()=>{try{
 const assert=(x,m)=>{if(!x)throw Error(m)};
 S=seed();S.projects=S.projects.slice(0,1);S.locks={};IX=null;ensureWorkspace();
 const p=S.projects[0],s=p.systems[0],a=s.acts[0],people=S.lib.people;
 s.stage='Р';s.scheme.num='ВК1-1';s.scheme.name='Устройство водоснабжения';s.code='ВК1';s.name='Система водоснабжения';p.cipher='2026-00000-01-0';s.cipher='';
 Object.assign(s.scheme,{file:'certificate.pdf',fileKey:ASSET,pages:3,frameEnabled:true,rd:''});
 Object.assign(a,{num:'АОСР-042',date:'2026-10-18',schemeLinks:[{id:'system',from:1,to:3}]});
 s.acts=[a];const v=volumeList(p).find(v=>v.s?.id===s.id),item=drawingRecord(s,'system');
 const choose=(selector,value)=>{const el=document.querySelector(selector);assert(el,'Missing signer control '+selector);el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));};
 history.replaceState(null,'','#/s/'+s.id+'/params');render();
 assert(!document.querySelector('[data-frame-signer="developed"]'),'System must not default developer');
 choose('[data-frame-signer="checked"]',people[1].id);choose('[data-frame-signer="controlled"]',people[2].id);
 s.frameSigners.developed=people[1].id;
 s.scheme.frameSigners={checked:people[0].id,controlled:''}; // Legacy overrides must not hide system settings.
 const old=A.drawingPreview;A.drawingPreview=()=>{};A.drawingEdit({s:s.id,x:'system'});A.drawingPreview=old;
 assert(document.querySelectorAll('.dlg [data-frame-signer]').length===1,'Only developer belongs in scheme editor');
 assert(document.querySelector('.dlg [data-frame-signer="developed"]').value==='','Developer must start empty');
 let cfg=drawingContext(p,s,item,v);assert(cfg.values.Разработал==='','No implicit developer from system or execution');
 assert(cfg.values.Проверил===shortFio(people[1].fio)&&cfg.values.Нормоконтроль===shortFio(people[2].fio),'System signers must win over legacy overrides');
 choose('.dlg [data-frame-signer="developed"]',people[0].id);
 cfg=drawingContext(p,s,item,v);assert(cfg.values.Разработал===shortFio(people[0].fio),'Explicit drawing developer');
 assert(cfg.values.Шифр==='2026-00000-01-0-ВК1'&&cfg.values.Система===s.name&&cfg.values.Стадия==='Р','Stamp field mapping');assert(cfg.values.Дата==='18.10.2026','Signature date from act');assert(cfg.values.АОСР===a.num&&cfg.values.Номер_Приложения==='1','Full source act resolution');
 choose('.dlg [data-frame-signer="developed"]','');assert(drawingContext(p,s,item,v).values.Разработал==='','Cleared developer must remain empty');
 choose('.dlg [data-frame-signer="developed"]',people[0].id);closeModal();
 s.cipher='2026-00000-01-0-ВК1';assert(drawingContext(p,s,item,v).values.Шифр===s.cipher,'Duplicate system suffix');
 const second={...a,id:'act-other',num:'АОСР-043',date:'2026-10-19',executionId:a.executionId,schemeLinks:[{id:'system',from:1,to:3}]};s.acts.push(second);s.scheme.frameActId=second.id;
 assert(drawingContext(p,s,item,v).values.АОСР===second.num,'Explicit act selection');assert(drawingContext(p,s,item,v,a).values.АОСР===a.num,'Export owner must win');
 const extra={...ROWT.scheme(a),id:'unlinked',name:'Отдельный чертёж',file:'certificate.pdf',fileKey:ASSET,pages:3,frameEnabled:true};s.sketches.push(extra);assert(drawingContext(p,s,drawingRecord(s,extra.id),v).values.АОСР==='','Unlinked drawing inherited an unrelated act');

 const plan=pdfPlan(p,[v]);const framed=plan.volumes.flatMap(v=>v.documents).filter(d=>d.id.startsWith('framed:system:'));
 assert(framed.length===2,'Shared drawing needs exactly one copy per act: '+framed.length);
 assert(framed.some(d=>d.frame.values.АОСР===a.num&&d.frame.values.Дата==='18.10.2026'),'First act stamp');
 assert(framed.some(d=>d.frame.values.АОСР===second.num&&d.frame.values.Дата==='19.10.2026'),'Second act stamp');
 assert(framed.every(d=>d.frame.values.Название_Схемы==='ВК1-1 · Устройство водоснабжения'),'Drawing number and name');
 assert(frameWarnings(plan).some(w=>w.includes('Разработал')),'Unassigned drawing developer warning');
 s.scheme.stage='ИД';assert(drawingContext(p,s,item,v).values.Стадия==='ИД','Scheme stage override');delete s.scheme.stage;
 s.acts=[a];delete s.scheme.frameActId;p.exportMode='custom';p.exportProfile='';
 const docs=assemblyActPlan(p,a.id,['schemes']).volumes.flatMap(v=>v.documents).filter(d=>d.id.startsWith('framed:system:'));assert(docs.length===1&&docs.every(d=>d.frame.values.АОСР===a.num),'Assembly lost attachment context');
 p.exportIssuer=S.lib.orgs[0].id;assert(drawingContext(p,s,item,v).values.Организация===(S.lib.orgs[0].full||S.lib.orgs[0].short),'Export company');
 save();await desktopFlush();const loaded=(await nativeCall('load')).state.projects[0].systems.find(x=>x.id===s.id);assert(loaded.frameSigners.checked===people[1].id&&loaded.scheme.frameSigners.developed===people[0].id&&loaded.stage==='Р'&&loaded.scheme.num==='ВК1-1','Frame settings lost on disk');
 const result=await nativeCall('previewDrawing',{key:ASSET,page:2,frame:drawingContext(p,s,item,v,a)});assert(result.pages===3&&result.image.startsWith('data:image/png'),'Native multi-page preview');
 const el={checked:false};A.drawingToggle({s:s.id,x:'system'},el);assert(!pdfSources(p,v).get('ss'+s.id).frame,'Frame toggle ignored');
 
 const warningPlan={volumes:[{documents:[{name:'Схема',frame:{values:{Разработал:'',Проверил:'',Нормоконтроль:''}}}]}]};
 let warning=confirmFrameWarnings([warningPlan]);closeModal();assert(await warning===false,'Closing warning should cancel');
 warning=confirmFrameWarnings([warningPlan]);document.querySelector('[data-mb="1"]').click();assert(await warning===true,'Continue warning');
 warning=confirmFrameWarnings([warningPlan]);document.querySelector('[data-mb="0"]').click();assert(await warning===false,'Cancel warning');
 await desktopFlush();window.frameResult={ok:true};
 }catch(e){window.frameResult={error:e.stack};}})();'''
 window.page.runJavaScript(script.replace('ASSET',json.dumps(asset['id'])))
def receive(value):
 global stage
 if stage!=1 or not value:return
 result=json.loads(value)
 if result.get('error'):fail(result['error']);return
 try:
  assert not window.page.console_errors,window.page.console_errors
  stage=2;timer.stop();print('PASS: explicit drawing developer, automatic system reviewers, legacy override handling, persistence, act context, native preview and warnings');window.close()
 except Exception:fail(traceback.format_exc())
def poll():
 if stage==0:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.frameResult?JSON.stringify(window.frameResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Frame test timed out'))
with patch('drawing_frame.resolve_frame_font',return_value='DejaVu Sans'):code=app.exec()
dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
