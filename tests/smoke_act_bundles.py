"""Act bundles use the same order in the UI, native PDF and single-act exports."""
import base64,json,sys,tempfile,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage
from pypdf import PdfWriter,PdfReader
from app import Window,dispose_window
from folder_store import Store
from pdf_export import prepare_export,write_export
app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);store=Store(root/'database')
w=PdfWriter();w.add_blank_page(210,297);w.add_blank_page(420,297);w.write(root/'source.pdf');w.close();asset=store.import_file(root/'source.pdf')
image=QImage(10,10,QImage.Format.Format_RGB32);image.fill(0xffffff);image.save(str(root/'photo.png'));photo='data:image/png;base64,'+base64.b64encode((root/'photo.png').read_bytes()).decode()
window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(error):errors.append(str(error));app.exit(1)
def ready(value):
 global stage
 if not value or stage:return
 stage=1
 script=r'''(()=>{try{
 const assert=(condition,message)=>{if(!condition)throw Error(message);};
 S=seed();S.projects=S.projects.slice(0,1);S.locks={};S.volCfg={};IX=null;ensureWorkspace();
 const p=S.projects[0];p.systems=p.systems.slice(0,1);p.admin=[];p.journals=[];p.surveys=[];p.opsDocs=[];p.materials=[];S.lib.orders=[];
 const s=p.systems[0],pf=S.lib.profiles[0];s.subprofiles=s.subprofiles.slice(0,1);s.aik=[];s.journals=[];s.trials=[];s.sketches=[];s.acts=s.acts.slice(0,2);
 Object.assign(s.scheme,{file:'source.pdf',fileKey:ASSET,pages:2,frameEnabled:false});
 const m={id:'bundle-material',name:'Труба',scope:'object',baseId:'',docs:[{id:'bundle-quality',type:'Сертификат',num:'100',file:'source.pdf',fileKey:ASSET,pages:2}]};p.materials=[m];
 const png=PHOTODATA;
 s.acts.forEach((a,i)=>Object.assign(a,{type:'АОСР',quantityEnabled:false,subs:[s.subprofiles[0].id],materials:[m.id],photos:[{id:'photo-'+i,img:png,cap:'Фото '+i}],schemes:[],schemeLinks:[{id:'system',from:i+1,to:i+1}],tests:[],testLinks:[],scan:{file:'',fileKey:''}}));
 p.exportMode='profile';p.exportProfile=pf.id;pf.quality='each';pf.exportSettings={order:EXPORT_BLOCKS.map(x=>x[0]),off:[]};
 const v=volumeList(p).find(v=>v.s?.id===s.id),act1=s.acts[0],act2=s.acts[1];
 const plan=()=>assemblyRules(p,pdfPlan(p,[v])),docs=()=>plan().volumes[0].documents.filter(d=>!['title','reg'].includes(d.id));
 let d=docs();assert(d.length===8,'Expected 2 acts with 3 attachments each: '+d.map(d=>d.id));
 for(let i=0;i<2;i++){const part=d.slice(i*4,i*4+4);assert(part[0].id==='a'+s.acts[i].id,'Act stays before its bundle');assert(part.slice(1).map(x=>x.sourceBlock).join(',')==='schemes,photos,quality','Default attachment order');assert(part[1].from===i+1&&part[1].to===i+1,'Selected range is preserved');}
 const c={scenario:'2',executions:p.executions.map(e=>e.id),systems:[s.id],sections:EXPORT_BLOCKS.map(x=>x[0]),act:act1.id};
 const html=assemblyOrderHtml(p,c);for(const item of d)assert(html.includes('data-assembly-document="'+item.id+'"'),'Preview hides '+item.id);
 pf.exportSettings.actAttachmentOrder=['quality','photos','schemes'];d=docs();assert(d.slice(1,4).map(x=>x.sourceBlock).join(',')==='quality,photos,schemes','Custom attachment order');
 pf.quality='once';const whole=assemblyRules(p,pdfPlan(p,volumeList(p)));const qualities=whole.volumes.flatMap(v=>v.documents).filter(d=>d.qualityId);assert(qualities.length===1&&qualities[0].ownerActId===act1.id,'Shared quality goes to first act, not T1');
 pf.quality='first';assert(docs().filter(d=>d.qualityId).length===1,'Quality first rule');
 pf.quality='each';let single=assemblyActPlan(p,act2.id,c.sections).volumes[0].documents;assert(single.filter(d=>d.sourceBlock==='schemes').length===1,'Single-act drawing not duplicated');assert(single.some(d=>d.sourceBlock==='photos'),'Single-act photo preserved');assert(!single.some(d=>d.id==='a'+act1.id),'Other act excluded');
 pf.exportSettings.off=['schemes'];assert(!docs().some(d=>d.sourceBlock==='schemes'),'Disabled schemes excluded');pf.exportSettings.off=['quality'];assert(!docs().some(d=>d.qualityId),'Disabled quality excluded');pf.exportSettings.off=[];
 pf.exportSettings.actSchemes='section';d=docs();assert(d.some(d=>d.block==='schemes')&&!d.some(d=>d.ownerActId),'Legacy section mode');
 pf.exportSettings.actSchemes='afterAct';pf.exportSettings.actAttachmentOrder=['schemes','photos','quality'];pf.quality='each';
 history.replaceState(null,'','#/lib/profiles/'+pf.id);render();assert(document.querySelector('[data-f="exportSettings.actSchemes"]'),'Profile option missing');assert(document.querySelectorAll('[data-a="actAttachmentMove"]').length===6,'Profile order controls missing');
 A.actAttachmentMove({id:pf.id,key:'quality',d:'-1'});assert(pf.exportSettings.actAttachmentOrder.join(',')==='schemes,quality,photos','Reorder action');
 pf.exportSettings.actAttachmentOrder=['schemes','photos','quality'];
 // An owned drawing remains in its act and is not emitted again in the common section.
 act1.schemes=[{id:'owned',name:'Схема к первому акту',file:'source.pdf',fileKey:ASSET,pages:2,frameEnabled:false}];
 assert(docs().filter(d=>d.sourceRecordId==='owned').length===1,'Owned drawing duplicated');act1.schemes=[];
 window.bundleResult={plan:plan(),ids:docs().map(d=>d.id)};
 }catch(e){window.bundleResult={error:e.stack||e.message};}})();'''.replace('ASSET',json.dumps(asset['id'])).replace('PHOTODATA',json.dumps(photo))
 window.page.runJavaScript(script)
def receive(raw):
 global stage
 if not raw:return
 try:
  result=json.loads(raw);assert not result.get('error'),result.get('error');assert not window.page.console_errors,window.page.console_errors
  prepared=prepare_export(store,result['plan']);documents=prepared['volumes'][0]['documents'];assert [d['id'] for d in documents if d['id'] not in ('title','reg')]==result['ids']
  ranges=[d for d in documents if d.get('sourceBlock')=='schemes'];assert [d['count'] for d in ranges]==[1,1]
  assert [tuple(d['reader'].pages[d['selection'][0]].mediabox)[2:] for d in ranges]==[(210,297),(420,297)]
  output=write_export(prepared,root/'bundle.pdf',store);assert len(PdfReader(output['path']).pages)==output['pages']
  assert [d['sourceBlock'] for d in documents if d.get('ownerActId')]==['schemes','photos','quality']*2
  stage=2;timer.stop();print('PASS: act bundles, selected ranges, profile ordering, preview, quality rules, exclusions, separate schemes, single act, native PDF');window.close()
 except Exception:fail(traceback.format_exc())
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.bundleResult?JSON.stringify(window.bundleResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Act bundles timed out'))
code=app.exec();dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
