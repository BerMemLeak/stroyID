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
 s.sectionDate='2026-09-15';s.stage='Р';s.scheme.num='ВК1-1';s.scheme.name='Устройство водоснабжения';s.code='ВК1';s.name='Система водоснабжения';p.cipher='2026-00000-01-0';s.cipher='';
 Object.assign(s.scheme,{file:'certificate.pdf',fileKey:ASSET,pages:3,frameEnabled:true,rd:''});
 Object.assign(a,{num:'АОСР-042',date:'2026-10-18',schemeLinks:[{id:'system',from:1,to:3}]});
 s.acts=[a];const v=volumeList(p).find(v=>v.s?.id===s.id),item=drawingRecord(s,'system');
 const choose=(selector,value)=>{const el=document.querySelector(selector);assert(el,'Missing signer control '+selector);el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));};
 s.frameSigners={checked:people[1].id,controlled:people[2].id,developed:people[1].id};
 s.scheme.frameSigners={checked:people[0].id,controlled:''}; // Ignore obsolete reviewer overrides.
 history.replaceState(null,'','#/s/'+s.id+'/params');render();
 assert(document.querySelectorAll('[data-frame-row-field="personId"]').length===3,'Legacy rows are available in system editor');
 const old=A.drawingPreview;A.drawingPreview=()=>{};A.drawingEdit({s:s.id,x:'system'});A.drawingPreview=old;
 assert(document.querySelectorAll('.dlg [data-frame-row-field]:disabled').length===6,'Inherited rows must be read-only until override');
 let cfg=drawingContext(p,s,item,v);assert(cfg.values.Разработал==='','No implicit legacy developer from system or execution');
 assert(cfg.values.Проверил===shortFio(people[1].fio)&&cfg.values.Нормоконтроль===shortFio(people[2].fio),'System legacy signers must win over obsolete overrides');
 document.querySelector('.dlg [data-a="frameRowsOverride"]').click();
 choose('.dlg [data-frame-row-field="personId"][data-row="0"]',people[0].id);
 cfg=drawingContext(p,s,item,v);assert(cfg.values.Разработал===shortFio(people[0].fio),'Explicit drawing developer');
 assert(cfg.values.Шифр==='2026-00000-01-0-ВК1'&&cfg.values.Система===s.name&&cfg.values.Стадия==='Р','Stamp field mapping');assert(cfg.values.Дата==='18.10.2026','Signature date from act');assert(cfg.values.АОСР===a.num&&cfg.values.Номер_Приложения==='1','Full source act resolution');
 choose('.dlg [data-frame-field="appNo"]','7');assert(drawingContext(p,s,item,v).values.Номер_Приложения==='7','Manual attachment override');
 choose('.dlg [data-frame-field="appNo"]','');assert(drawingContext(p,s,item,v).values.Номер_Приложения==='1','Clear override restores automatic number');
 const originalEntries=actAttachmentEntries;actAttachmentEntries=(act,section)=>[{name:'Другой документ',pages:1},...originalEntries(act,section)];
 assert(drawingContext(p,s,item,v).values.Номер_Приложения==='2','Number must use full AOSR attachment list');actAttachmentEntries=originalEntries;
 choose('.dlg [data-frame-row-field="personId"][data-row="0"]','');assert(drawingContext(p,s,item,v).values.Разработал==='','Cleared developer must remain empty');
 choose('.dlg [data-frame-row-field="personId"][data-row="0"]',people[0].id);closeModal();
 s.scheme.rd='Рабочая документация «Система водоснабжения», шифр ДРУГОЙ';
 assert(!drawingContext(p,s,item,v).values.Шифр.includes('Рабочая документация'),'RD description leaked into cipher');
 s.scheme.frameCipher='Отдельный-01';assert(drawingContext(p,s,item,v).values.Шифр==='Отдельный-01','Explicit frame cipher');delete s.scheme.frameCipher;
 a.schemes=[];const list=appsText(a,s);assert(list.includes('1. Исполнительная схема № ВК1-1 «Устройство водоснабжения», 3 л.'),'Full attachment list: '+list);
 assert(wordContext(p,v,'a'+a.id).values.Приложения===list,'Word attachment tags differ');
 const fullLinks=a.schemeLinks;a.schemeLinks=[{id:'system',from:2,to:3}];assert(appsText(a,s).includes(', 2 л.'),'Attachment count must use selected pages');
 a.schemeLinks.push({id:'system',from:1,to:2});assert(appsText(a,s).includes(', 3 л.')&&!appsText(a,s).includes('2. Исполнительная'),'Overlapping selections must count unique pages once');a.schemeLinks=fullLinks;
 const ctxTags=wordContext(p,v,'a'+a.id).values;assert(ctxTags.Реквизиты_Организации_Подписант_1.includes('ИНН')&&ctxTags.Полномочия_Подписант_1!==undefined,'Organization and authority tags');

 s.cipher='2026-00000-01-0-ВК1';assert(drawingContext(p,s,item,v).values.Шифр===s.cipher,'Duplicate system suffix');
 const second={...a,id:'act-other',num:'АОСР-043',date:'2026-10-19',executionId:a.executionId,schemeLinks:[{id:'system',from:1,to:3}]};s.acts.push(second);s.scheme.frameActId=second.id;
 assert(drawingContext(p,s,item,v).values.АОСР===second.num,'Explicit act selection');assert(drawingContext(p,s,item,v,a).values.АОСР===a.num,'Export owner must win');
 const extra={...ROWT.scheme(a),id:'unlinked',name:'Отдельный чертёж',file:'certificate.pdf',fileKey:ASSET,pages:3,frameEnabled:true};s.sketches.push(extra);assert(drawingContext(p,s,drawingRecord(s,extra.id),v).values.АОСР==='','Unlinked drawing inherited an unrelated act');

 const sectionCfg=drawingContext(p,s,drawingRecord(s,extra.id),v);
 assert(sectionCfg.values.Основание_Приложения==='К разделу'&&sectionCfg.values.Шифр_Приложения===s.cipher,'Section cipher mapping');
 assert(sectionCfg.values.Дата==='15.09.2026'&&sectionCfg.values.Дата_Приложения==='"15" 09.2026г.'&&sectionCfg.values.Номер_Приложения==='1','Section date and automatic number');
 assert(drawingContext(p,s,item,v,a).values.Дата_Приложения==='"18" 10.2026г.','Act date formatting');
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
 save();await desktopFlush();const loaded=(await nativeCall('load')).state.projects[0].systems.find(x=>x.id===s.id);assert(loaded.sectionDate==='2026-09-15'&&loaded.frameSigners.checked===people[1].id&&loaded.scheme.frameRows[0].personId===people[0].id&&loaded.stage==='Р'&&loaded.scheme.num==='ВК1-1','Frame settings lost on disk');
 // Two rows need no norm-control warning, repeated roles and all six slots work.
 s.frameRows=[{role:'Разработал',personId:people[0].id},{role:'Проверил',personId:people[1].id}];
 delete s.scheme.frameRows;delete s.scheme.frameSigners;
 cfg=drawingContext(p,s,item,v,a);assert(cfg.signerRows.length===2&&frameWarnings({volumes:[{documents:[{name:'Схема',frame:cfg}]}]}).length===0,'Two complete rows must not require norm-control');
 A.drawingEdit({s:s.id,x:'system'});document.querySelector('.dlg [data-a="frameRowsOverride"]').click();
 for(let i=0;i<4;i++)document.querySelector('.dlg [data-a="frameRowAdd"]').click();
 assert(s.scheme.frameRows.length===6&&document.querySelector('.dlg [data-a="frameRowAdd"]').disabled,'Physical six-row limit');
 A.frameRowAdd({s:s.id,x:'system'});assert(s.scheme.frameRows.length===6,'Limit must also be enforced by action handler');
 const roleInput=document.querySelector('.dlg [data-frame-row-field="role"][data-row="2"]');roleInput.focus();
 roleInput.value='Рук. проекта';roleInput.dispatchEvent(new Event('input',{bubbles:true}));
 assert(roleInput.isConnected&&document.activeElement===roleInput,'Role typing must preserve focus');
 ['Производ. работ','Строит. контроль','Строит. контроль'].forEach((role,i)=>{
   const el=document.querySelector('.dlg [data-frame-row-field="role"][data-row="'+(i+3)+'"]');el.value=role;el.dispatchEvent(new Event('input',{bubbles:true}));
 });
 for(let i=2;i<6;i++)choose('.dlg [data-frame-row-field="personId"][data-row="'+i+'"]',people[i%people.length].id);
 cfg=drawingContext(p,s,item,v,a);assert(cfg.signerRows.length===6&&cfg.signerRows[4].role===cfg.signerRows[5].role,'Repeated roles must remain separate');
 document.querySelector('.dlg [data-a="frameRowMove"][data-row="2"][data-step="-1"]').click();
 assert(s.scheme.frameRows[1].role==='Рук. проекта'&&s.frameRows.length===2,'Reordering must not mutate inherited system rows');
 save();await desktopFlush();const persisted=(await nativeCall('load')).state.projects[0].systems.find(x=>x.id===s.id);
 assert(persisted.scheme.frameRows.length===6&&persisted.scheme.frameRows[1].role==='Рук. проекта','Ordered rows lost on disk');
 const result=await nativeCall('previewDrawing',{key:ASSET,page:2,frame:drawingContext(p,s,item,v,a)});assert(result.pages===3&&result.image.startsWith('data:image/png'),'Native multi-page preview');
 document.querySelector('.dlg [data-a="frameRowRemove"][data-row="5"]').click();assert(s.scheme.frameRows.length===5&&!document.querySelector('.dlg [data-a="frameRowAdd"]').disabled,'Deleting must free a slot');
 document.querySelector('.dlg [data-a="frameRowsInherit"]').click();assert(!s.scheme.frameRows&&frameSignerRows(s,item).length===2,'Return to system rows');
 s.frameRows[0].personId=people[2].id;assert(drawingContext(p,s,item,v,a).signerRows[0].name===shortFio(people[2].fio),'Inheritance must follow future system changes');
 closeModal();
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
  stage=2;timer.stop();print('PASS: configurable frame rows, six-slot limit, inheritance, migration, typing focus, persistence, native preview and act context');window.close()
 except Exception:fail(traceback.format_exc())
def poll():
 if stage==0:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.frameResult?JSON.stringify(window.frameResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Frame test timed out'))
with patch('drawing_frame.resolve_frame_font',return_value='DejaVu Sans'):code=app.exec()
dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
