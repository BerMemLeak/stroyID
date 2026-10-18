"""Independent execution cards, native frame preview and all twelve export workflows."""
import io,json,sys,tempfile,traceback,zipfile,csv,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from pypdf import PdfWriter,PdfReader
from app import Window,dispose_window
from folder_store import Store
from drawing_frame import MM,TEMPLATE
from pdf_text import page_text
app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);store=Store(root/'database');writer=PdfWriter();writer.add_blank_page(210*MM,297*MM);writer.add_blank_page(420*MM,297*MM);writer.write(root/'scheme.pdf');asset=store.import_file(root/'scheme.pdf');(root/'frame.html').write_bytes(TEMPLATE.read_bytes());window=Window(store,test_profile=True);window.show();stage=0;errors=[];saved=[]
def fail(x):errors.append(str(x));app.exit(1)
def destination(*args):
 ext='.pdf' if 'PDF' in args[-1] else '.zip' if 'ZIP' in args[-1] else '.csv' if 'CSV' in args[-1] else '.xlsx';path=root/('export-'+str(len(saved)+1)+ext);saved.append(path);return str(path),args[-1]
def ready(v):
 global stage
 if not v or stage:return
 stage=1
 script=r'''(async()=>{try{
 S=seed();S.projects=S.projects.slice(0,1);S.locks={};S.lib.orders=[];S.lib.base=[];S.volCfg={};IX=null;ensureWorkspace();const p=S.projects[0];p.systems=p.systems.slice(0,1);p.admin=[];p.journals=[];p.surveys=[];p.opsDocs=[];p.materials=[];p.exportMode='custom';p.exportProfile='';const s=p.systems[0],e1=p.executions[0];s.code='ВК';s.aik=[];s.journals=[];s.sketches=[];s.trials=[];s.subprofiles=s.subprofiles.slice(0,1);s.acts=s.acts.slice(0,1);const a=s.acts[0];Object.assign(a,{type:'АОСР',works:'Первое выполнение',subs:[s.subprofiles[0].id],materials:[],tests:[],photos:[],schemes:[],testLinks:[],scan:{file:'',pages:0},schemeLinks:[{id:'system',from:1,to:1}]});Object.assign(s.scheme,{file:'scheme.pdf',fileKey:ASSET,pages:2,frameEnabled:true});
 A.executionEdit({p:p.id,e:e1.id});document.querySelector('#execution-name').value='Монтаж — первый этап';document.querySelector('#execution-start').value='2026-10-12';MB[1].f();
 A.executionAdd({p:p.id});document.querySelector('#execution-name').value='Монтаж — второй этап';document.querySelector('#execution-start').value='2026-10-15';MB[1].f();const e2=p.executions.at(-1);A.newSystem({p:p.id,e:e2.id});document.querySelector('input[name=ns][value="ВК"]').checked=true;MB[1].f();const s2=p.systems.at(-1);A.newAct({s:s2.id});MB[1].f();const a2=s2.acts[0];Object.assign(a2,{works:'Второе выполнение',materials:[],schemeLinks:[{id:'system',from:2,to:2}]});Object.assign(s2.scheme,{file:'scheme.pdf',fileKey:ASSET,pages:2,frameEnabled:true});
 // Explicit fixture signers keep the real frame/export checks unattended.
 const signerIds=S.lib.people.slice(0,3).map(person=>person.id);
 if(signerIds.length!==3)throw Error('Missing fixture signers');
 for(const system of [s,s2])system.frameSigners={developed:signerIds[0],checked:signerIds[1],controlled:signerIds[2]};
 const material={id:'base-test',name:'Труба',baseId:'',brand:'',maker:'',category:'Труба',docs:[{id:'quality-test',type:'Паспорт',num:'123',date:'2026-10-12',file:'scheme.pdf',fileKey:ASSET,pages:2}]};S.lib.base.push(material);p.materials.push({id:'mat-test',baseId:material.id,name:material.name,docs:[]});a.materials=['mat-test'];a2.materials=['mat-test'];
 const common={id:'order-test',name:'Общий приказ',num:'1',date:'2026-10-12',file:'scheme.pdf',fileKey:ASSET,pages:2};p.admin=[common];save();await desktopFlush(true);
 if(p.systems.length!==2||s.id===s2.id||s.subprofiles[0].id===s2.subprofiles[0].id||a.executionId===a2.executionId)throw Error('Independent card allocation failed');
 for(const e of p.executions){history.replaceState(null,'','#/e/'+p.id+'/'+e.id);render();if(document.querySelector('#content [data-a="assemblyRun"]')||document.querySelector('#content [data-ent="exec"][data-f="stage"]'))throw Error('Execution contains export or workflow stages');}
 history.replaceState(null,'','#/s/'+s2.id+'/params');render();if(!document.querySelector('#content [data-ent="sys"][data-f="name"]'))throw Error('Complete system editor missing');
 await A.drawingTemplatePick({s:s2.id,x:'system'});closeModal();await desktopFlush(true);const preview=await nativeCall('previewDrawing',{key:s2.scheme.fileKey,page:2,frame:drawingContext(p,s2,resourceList(s2)[0],volumeList(p).find(v=>v.s?.id===s2.id),a2)});if(preview.width!==420||preview.height!==297||!preview.image.startsWith('data:image/png'))throw Error('Real frame preview failed');
 await folderMutation('trashMove',{ent:'sys',id:s.id});if(p.systems.length!==1||p.systems[0].id!==s2.id)throw Error('Other execution was changed');const removed=S.trash.find(t=>t.ent==='sys');await folderMutation('trashRestore',{id:removed.id,restoreParents:true});if(p.systems.length!==2)throw Error('System restore failed');
 const pf=S.lib.profiles[0];p.exportProfile=pf.id;p.exportMode='profile';pf.exportSettings={order:EXPORT_BLOCKS.map(x=>x[0]),off:[],common:'once'};pf.quality='once';let c={scenario:'2',executions:p.executions.map(e=>e.id),systems:p.systems.map(s=>s.id),sections:EXPORT_BLOCKS.map(x=>x[0]),act:a.id,format:'xlsx'};
 const count=(plan,f)=>plan.volumes.flatMap(v=>v.documents).filter(f).length;let rule=assemblyPlans(p,c)[0].plan;if(count(rule,d=>d.qualityId)!==1||count(rule,d=>d.id==='adminorder-test')!==1)throw Error('Once-only profile rules failed '+JSON.stringify(rule.volumes.map(v=>({kind:v.kind,docs:v.documents.map(d=>[d.id,d.qualityId,d.qualityMode])}))));pf.exportSettings.common='each';pf.quality='each';rule=assemblyPlans(p,c)[0].plan;if(count(rule,d=>d.qualityId)!==2||count(rule,d=>d.id==='adminorder-test')!==2)throw Error('Each-execution/act profile rules failed');pf.quality='first';if(count(assemblyPlans(p,c)[0].plan,d=>d.qualityId)!==1)throw Error('First-act quality rules failed');pf.exportSettings.common='none';if(count(assemblyPlans(p,c)[0].plan,d=>d.common)!==0)throw Error('Common-none rule failed');pf.exportSettings.common='once';pf.quality='once';p.exportMode='profile';save();await desktopFlush(true);

 const assertOrder=()=>{
  const expected=assemblyPlans(p,assemblyPick(p)).flatMap(x=>x.plan.volumes);
  const actual=[...document.querySelectorAll('[data-assembly-volume]')];
  if(JSON.stringify(actual.map(x=>x.dataset.assemblyVolume))!==JSON.stringify(expected.map(v=>v.key)))throw Error('Order volumes differ from exported plan');
  const ids=actual.map(x=>[...x.querySelectorAll('[data-assembly-document]')].map(d=>d.dataset.assemblyDocument));
  const wanted=expected.map(v=>v.documents.filter(d=>!['title','reg'].includes(d.id)).map(d=>d.id));
  if(JSON.stringify(ids)!==JSON.stringify(wanted))throw Error('Order documents differ from exported plan');
  const order=document.querySelector('[data-assembly-order]'),button=document.querySelector('[data-a="assemblyRun"]');
  if(!(order.compareDocumentPosition(button)&Node.DOCUMENT_POSITION_FOLLOWING))throw Error('Order must precede export buttons');
 };
 Object.assign(assemblyPick(p),{scenario:'2',executions:[e1.id,e2.id],systems:[s.id,s2.id],includeCommon:true,includeOperations:true});
 history.replaceState(null,'','#/build/'+p.id);render();assertOrder();
 p.exportMode='custom';
 const rememberedVolume=volumeList(p).find(v=>v.kind==='T2');S.volCfg[p.id+'|'+rememberedVolume.key]={order:blocksFor(p,rememberedVolume).map(b=>b.key).reverse()};
 const orderBefore=JSON.stringify(S.volCfg);
 for(const key of ['includeCommon','includeOperations']){const toggle=document.querySelector('[data-assembly="'+key+'"]');toggle.checked=false;toggle.dispatchEvent(new Event('change',{bubbles:true}));assertOrder();}
 if([...document.querySelectorAll('[data-assembly-volume]')].some(x=>x.textContent.includes('Том 1.')||x.textContent.includes('Том 3.')))throw Error('Disabled volumes remain in order');
 for(const key of ['includeCommon','includeOperations']){const toggle=document.querySelector('[data-assembly="'+key+'"]');toggle.checked=true;toggle.dispatchEvent(new Event('change',{bubbles:true}));assertOrder();}
 if(JSON.stringify(S.volCfg)!==orderBefore)throw Error('Toggling volumes reset document order');
 Object.assign(assemblyPick(p),{scenario:'4',executions:[e2.id],systems:[s2.id]});render();assertOrder();
 const chosen=assemblyPlans(p,assemblyPick(p)).flatMap(x=>x.plan.volumes);if(chosen.some(v=>v.kind==='T2'&&!v.key.endsWith(s2.subprofiles[0].id)))throw Error('Unselected system in order');

 const selectedVolume=volumeList(p).find(v=>v.s?.id===s2.id);
 A.assemblyBlock({p:p.id,v:selectedVolume.key,k:'schemes'},{checked:false});assertOrder();
 if(!document.querySelector('[data-assembly-excluded] [data-k="schemes"]'))throw Error('Excluded section cannot be restored');
 A.assemblyBlock({p:p.id,v:selectedVolume.key,k:'schemes'},{checked:true});assertOrder();
 p.exportMode='profile';
 const results=[];for(let n=1;n<=12;n++){const c=assemblyPick(p);Object.assign(c,{scenario:String(n),executions:[e1.id,e2.id],systems:[s.id,s2.id],sections:EXPORT_BLOCKS.map(x=>x[0]),act:a.id,format:'xlsx'});if([1,4,5,9].includes(n))c.executions=[e1.id];if(n===4)c.systems=[s.id];if(n===9)c.attachments=[];else delete c.attachments;history.replaceState(null,'','#/build/'+p.id);render();if(n!==11)assertOrder();const plans=assemblyPlans(p,c);const warnings=plans.flatMap(x=>frameWarnings(x.plan));if(warnings.length)throw Error('Scenario '+n+' has missing fixture signers: '+warnings.join('; '));const result=await A.assemblyRun({p:p.id});if(!result)throw Error('Scenario '+n+': '+document.querySelector('#modal-root').innerText);results.push({...result,scenario:n});closeModal();}
 assemblyPick(p).format='csv';const csv=await A.assemblyRun({p:p.id});if(!csv)throw Error('CSV registry failed');closeModal();go('#/build/'+p.id);render();window.executionResult={ok:true,results,csv,pid:p.id};
 }catch(e){window.executionResult={error:e.stack};}})();'''.replace('ASSET',json.dumps(asset['id']))
 window.page.runJavaScript(script)
def receive(v):
 global stage
 if stage!=1 or not v or v=='null':return
 result=json.loads(v)
 if result.get('error'):fail(result);return
 try:
  state=store.load()['state'];p=state['projects'][0];assert len(p['systems'])==2 and len(p['executions'])==2;assert p['executions'][0]['name']=='Монтаж — первый этап';assert not any(e.get('allocations') for e in p['executions']);assert not window.page.console_errors,window.page.console_errors
  for entry in result['results']:
   file=Path(entry['path']);assert file.is_file();n=entry['scenario']
   if n not in (7,8,11,12):assert len(PdfReader(file).pages)==entry['pages']
   if n in (7,8):
    with zipfile.ZipFile(file) as z:
     assert len(z.namelist())==2;assert all(PdfReader(io.BytesIO(z.read(name))).pages for name in z.namelist())
   if n==11:
    with zipfile.ZipFile(file) as z:z.extractall(root/'other-pc')
    other=Store(root/'other-pc/СтройИД');loaded=other.load();assert not loaded['warnings'];assert len(loaded['state']['projects'][0]['systems'])==2;assert len(loaded['state']['lib']['base'])==1;other.close()
   if n==12:
    with zipfile.ZipFile(file) as z:
     assert z.testzip() is None;sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));assert len(sheet.findall('.//{*}row'))==entry['documents']+1
  text=''.join(page_text(page) for page in PdfReader(result['results'][0]['path']).pages);assert 'Первое выполнение' in text and 'Второе выполнение' not in text
  whole=PdfReader(result['results'][1]['path']);assert len(whole.pages)>len(PdfReader(result['results'][0]['path']).pages)
  rows=list(csv.reader(Path(result['csv']['path']).read_text('utf-8-sig').splitlines(),delimiter=';'));assert len(rows)==result['csv']['documents']+1;assert int(rows[-1][5])==result['csv']['pages']
  window.grab().save(str(root/'assembly.png'));stage=2;timer.stop();print('PASS: independent same-code systems, editable executions, single shared passport, trash restore, real GOST preview, all 12 export scenarios, profile repetition rules, actual XLSX/CSV registry, portable ZIP on another folder');window.close()
 except Exception:fail(traceback.format_exc())
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript("JSON.stringify(window.executionResult||(document.querySelector('[data-frame-warning]')?{error:'Unexpected signer warning: test fixtures must provide all frame signers'}:null))",receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(200);QTimer.singleShot(90000,lambda:fail('Execution/export UI timed out'))
# Substitute a free test font only for geometry; production still requires ISOCPEUR.
with patch('drawing_frame.resolve_frame_font', return_value='DejaVu Sans'), patch('app.QFileDialog.getSaveFileName',side_effect=destination),patch('app.QFileDialog.getOpenFileName',return_value=(str(root/'frame.html'),'HTML')):code=app.exec()
dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
