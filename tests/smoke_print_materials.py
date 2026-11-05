"""Real Qt UI: template download, two-document import, and overflow confirmation/retry."""
import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from stroyid.presentation.desktop.window import Window,dispose_window
from stroyid.infrastructure.storage import Store
from test_print_materials import fixture_xlsx,pdf

app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name)
pdf(root/'passport.pdf',[(595,842)]);pdf(root/'certificate.pdf',[(842,1191)])
fixture_xlsx(root/'materials.xlsx',[['M-UI','Материал UI','','Паспорт качества','','','passport.pdf','Сертификат соответствия','123','','certificate.pdf']])
store=Store(root/'database');window=Window(store,test_profile=True);window.show();started=False;result=None
script=r'''(async()=>{try{
 const assert=(v,m)=>{if(!v)throw Error(m);};S=seed();IX=null;ensureWorkspace();
 const p=S.projects[0],s=p.systems[0],a=s.acts[0];a.type='АОСР';a.quantityEnabled=false;
 save();await desktopFlush();go('#/lib/base');render();
 assert(document.querySelector('[data-a="materialsTemplate"]'),'Template button missing');
 await A.materialsTemplate();await A.materialsImport();
 assert(materialImportPreview?.items[0].docs.length===2,'Two docs not reviewed');
 assert(!materialImportPreview.errors.length,materialImportPreview.errors.join('; '));
 await A.materialsCommit();
 assert(S.lib.base.find(x=>x.name==='Материал UI')?.docs.length===2,'Two-document material not imported');
 const base=S.lib.base.find(x=>x.name==='Материал UI');
 for(const [id,name] of [['share-one','SHARE первый'],['share-two','SHARE второй']]){
  const m=structuredClone(base);Object.assign(m,{id,name,baseId:'',scope:'object'});m.docs.forEach(d=>d.id=uid());p.materials.push(m);
 }
 base.name='SHARE общий';p.materials.push({id:'already-common',baseId:base.id,docs:[],scope:'common'});
 a.materials=['share-one','share-two'];S.ui.f['mq'+p.id]='SHARE';S.ui.materialSource=S.ui.materialSource||{};S.ui.materialSource[p.id]='all';
 save();await desktopFlush();go('#/p/'+p.id+'/mats');render();
 assert(document.querySelector('[data-material-select="already-common"]').disabled,'Common material must not be promoted twice');
 const beforeHash=location.hash;document.querySelector('[data-material-select="share-one"]').click();
 assert(location.hash===beforeHash&&objectMaterialSelections.get(p.id).size===1,'Checkbox navigated instead of selecting');
 document.querySelector('[data-material-select-all]').click();
 assert(objectMaterialSelections.get(p.id).size===2,'Select-all included a common material or lost selection');
 const ids=a.materials.join(',');A.materialsShare({p:p.id});await desktopFlush();
 assert(a.materials.join(',')===ids,'Act material IDs changed');
 for(const id of ['share-one','share-two']){const m=p.materials.find(x=>x.id===id);assert(m.baseId&&m.docs.length===0&&mDocs(m).length===2,'Promotion lost documents or object links');}
 const loaded=await nativeCall('load');assert(!loaded.conflicts.length,'Promotion created conflicts');
 await A.desktopSave();go('#/a/'+a.id);render();assert(document.querySelectorAll('[data-act-register]').length===3,'Register controls missing');
 const v=volumeList(p).find(v=>v.s?.id===s.id),plan=pdfPlan(p,[v]),doc=plan.volumes[0].documents.find(d=>d.id==='a'+a.id);
 assert(doc.actRegister?.actId===a.id,'No act metadata');
 A.printSetup({p:p.id});assert(!document.querySelector('#print-number').checked,'Page numbers should default off');
 assert(document.querySelector('[data-print-type="АОСР"]').value==='duplex','Act duplex default');
 assert(!document.querySelector('[data-print-doc]')&&!document.querySelector('#modal-root').innerText.includes('Переопределить отдельные документы'),'Per-document print overrides remain');
 closeModal();
 let calls=0;const request=desktop.request;
 desktop.request=(op,raw,cb)=>{if(op!=='exportPdf')return request(op,raw,cb);calls++;
  const payload=JSON.parse(raw);
  if(calls===1)return cb(JSON.stringify({ok:false,error:'overflow',details:[{kind:'actOverflow',actId:a.id,number:a.num,pages:3,suggested:['attachments']}]}));
  assert(payload.plan.volumes[0].documents.find(d=>d.id==='a'+a.id).actRegister.settings.attachments.enabled,'Retry lost chosen register');
  cb(JSON.stringify({ok:true,value:{passed:true}}));
 };
 const pending=nativeCall('exportPdf',{plan});
 await new Promise(r=>setTimeout(r,50));assert(MB[1]?.l==='Применить и пересобрать','No overflow proposal');MB[1].f();closeModal();
 const exported=await pending;desktop.request=request;
 assert(exported.passed&&calls===2,'No export retry');assert(getEnt('act',a.id).registers.attachments.enabled,'Choice not persisted');
 window.printMaterialsResult=JSON.stringify({ok:true});
 }catch(e){window.printMaterialsResult=JSON.stringify({ok:false,error:e.stack});}})();'''
def begin(ok):
 global started
 if ok and not started:started=True;window.page.runJavaScript(script)
def finish(value):
 global result
 if value:
  result=json.loads(value);print(result,flush=True);app.exit(0 if result.get('ok') else 1)
def tick():
 if not started:window.page.runJavaScript('window.desktopReady===true',begin)
 else:window.page.runJavaScript('window.printMaterialsResult||null',finish)
timer=QTimer();timer.timeout.connect(tick);timer.start(100);QTimer.singleShot(90000,app.quit)
with patch('stroyid.presentation.desktop.window.QFileDialog.getOpenFileName',return_value=(str(root/'materials.xlsx'),'')), \
     patch('stroyid.presentation.desktop.window.QFileDialog.getExistingDirectory',return_value=str(root)), \
     patch('stroyid.presentation.desktop.window.QFileDialog.getSaveFileName',return_value=(str(root/'download-template.xlsx'),'')):
 app.exec()
assert result and result.get('ok'),result
assert (root/'download-template.xlsx').read_bytes()==(Path(__file__).resolve().parents[1]/'ui/reference-templates/materials-import.xlsx').read_bytes()
assert not window.page.console_errors,window.page.console_errors
loaded=store.load()
for material in loaded['state']['lib']['base']:
 if material['name'].startswith('SHARE'):
  assert len(material['docs'])==2
  for document in material['docs']:assert store.asset_path(document['fileKey'])[0].is_file()
dispose_window(window);store.close();tmp.cleanup();print('PRINT / MATERIALS UI PASS',flush=True)
