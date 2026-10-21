"""Exercise multi-row editing, per-act inclusion, templates and native DOCX/PDF output."""
import html,json,sys,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app import Window,dispose_window
from storage import Store
from word_templates import inspect_docx,package
from pdf_export import prepare_export,render_html
from pdf_text import page_text
application=QApplication.instance() or QApplication([])
work=tempfile.TemporaryDirectory();root=Path(work.name);store=Store(root/'data')
window=Window(store,test_profile=True);window.show();stage=0;errors=[];rendered=[]
def fail(e):errors.append(str(e));application.exit(1)
def ready(ok):
 global stage
 if stage or not ok:return
 stage=1
 script=r'''(async()=>{try{
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
 S=seed();S.projects=S.projects.slice(0,1);S.locks={};IX=null;ensureWorkspace();
 const p=S.projects[0];p.systems=p.systems.slice(0,1);p.admin=[];p.journals=[];p.surveys=[];p.opsDocs=[];p.materials=[];
 const s=p.systems[0];s.subprofiles=s.subprofiles.slice(0,1);s.aik=[];s.journals=[];s.sketches=[];s.trials=[];s.scheme.file='';s.scheme.fileKey='';s.acts=s.acts.slice(0,1);
 const a=s.acts[0];Object.assign(a,{type:'АОСР',subs:[s.subprofiles[0].id],materials:[],scan:{file:'',pages:0},schemes:[],tests:[],testLinks:[],schemeLinks:[],photos:[]});
 S.volCfg={};ensureWorkspace();save();await desktopFlush(true);go('#/a/'+a.id+'/quantity');render();
 assert(document.querySelector('[data-quantity-toggle]')?.checked,'Quantity tab not visible/enabled');
 assert(quantityIssues(a).length>0,'Missing quantity data accepted');
 for(const [key,value] of Object.entries({name:'Монтаж трубы',place:'Этаж 1',unit:'м',qty:'12,5'})){
  const input=document.querySelector('[data-quantity-field="'+key+'"]');input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));
 }
 A.quantityAdd({id:a.id});const row=a.quantityRows[1];Object.assign(row,{name:'Монтаж хомутов',place:'Этаж 2',unit:'шт.',qty:'20'});save();
 assert(!quantityIssues(a).length,'Valid rows rejected');
 const v=volumeList(p).find(v=>v.s),ctx=wordContext(p,v,'quantity:'+a.id);
 assert(ctx.collections.Объемы.length===2&&ctx.collections.Объемы[0].Количество==='12,5','Rows lost');
 assert(ctx.values['Подписанты.ИсполнительРабот.ФамилияИнициалы']&&ctx.values['Подписанты.СтройконтрольПодрядчика.ФамилияИнициалы'],'Act signers missing');
 const plan=pdfPlan(p,[v]),docs=plan.volumes[0].documents,actIndex=docs.findIndex(d=>d.id==='a'+a.id),q=docs[actIndex+1];
 assert(q.id==='quantity:'+a.id&&q.builtinTemplate==='quantity','Wrong attachment order/source');
 assert(docs[actIndex].html.includes(quantityMarker(a)),'Act has no page marker');
 const custom=await nativeCall('referenceTemplate',{section:'quantity'});
 const t={id:uid(),name:'Моя ведомость',type:'Ведомость объёмов работ',section:'quantity',fileKey:custom.id};S.lib.templates.push(t);p.wordTemplates.quantity=t.id;
 assert(quantitySource(p,s,a,v).templateKey===custom.id,'Custom template ignored');
 await A.quantityDownload({id:a.id});
 a.quantityEnabled=false;assert(!appsText(a,s).includes('Ведомость'),'Disabled sheet still listed');
 assert(!pdfPlan(p,[v]).volumes[0].documents.some(d=>d.id==='quantity:'+a.id),'Disabled sheet exported');
 a.quantityEnabled=true;a.type='АООК';assert(!quantityEnabled(a),'AOOK unexpectedly enabled');a.type='АОСР';
 const conf={...assemblyPick(p),scenario:'9',act:a.id,sections:['aosr','schemes','tests','photos'],attachments:[]};
 const filtered=assemblyPlans(p,conf)[0].plan.volumes[0].documents.find(d=>d.id==='a'+a.id);
 assert(!filtered.attachmentPageRefs&&!filtered.html.includes('Ведомость объёмов'),'Excluded sheet still referenced');
 await desktopFlush(true);const loaded=await nativeCall('load');
 assert(loaded.state.projects[0].systems[0].acts[0].quantityRows.length===2,'Rows not persisted');
 window.quantityResult=JSON.stringify({ok:true,plan});
 }catch(e){window.quantityResult=JSON.stringify({ok:false,error:e.stack});}})();'''
 window.page.runJavaScript(script)
def converter(jobs):
 for source,target in jobs:
  data=Path(source).read_bytes();assert not inspect_docx(data)['tags']
  text=' '.join(ET.fromstring(package(data)['word/document.xml']).itertext());rendered.append(text)
  render_html('<p>'+html.escape(text)+'</p>',target)
def finished(value):
 global stage
 if stage!=1 or not value:return
 try:
  result=json.loads(value);assert result['ok'],result
  assert not inspect_docx((root/'quantity.docx').read_bytes())['tags']
  with patch('pdf_export.convert_docx_batch',side_effect=converter):prepared=prepare_export(store,result['plan'])
  docs=prepared['volumes'][0]['documents'];q=next(d for d in docs if d['id'].startswith('quantity:'));a=docs[docs.index(q)-1]
  assert 'Монтаж трубы' in rendered[0] and 'Монтаж хомутов' in rendered[0]
  assert '[[QUANTITY_SHEETS:' not in a['html']
  assert 'Ведомость объёмов' in '\n'.join(page_text(page) for page in a['reader'].pages), 'Attachment absent from act PDF'
  assert not window.page.console_errors,window.page.console_errors
  print('PASS: quantity rows, editing, signers, inclusion, order, page counts, custom template, native DOCX download and persistence')
  stage=2;timer.stop();window.close()
 except Exception as e:fail(e)
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady===true',ready)
 elif stage==1:window.page.runJavaScript('window.quantityResult||null',finished)
timer=QTimer();timer.timeout.connect(poll);timer.start(100)
QTimer.singleShot(90000,lambda:fail('Quantities smoke timed out'))
with patch('app.QFileDialog.getSaveFileName',return_value=(str(root/'quantity.docx'),'Word')):code=application.exec()
dispose_window(window);store.close();work.cleanup()
if errors:print('\n'.join(errors),file=sys.stderr)
sys.exit(1 if errors or stage != 2 else code)
