"""Real UI acceptance: contextual tags, source isolation and every main screen."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app import Window,dispose_window
from storage import Store
app=QApplication([]);tmp=tempfile.TemporaryDirectory();store=Store(Path(tmp.name)/'db')
window=Window(store,test_profile=True);window.resize(1400,1000);window.show();stage=0;errors=[]
def fail(e): errors.append(str(e));app.exit(1)
def ready(ok):
 global stage
 if not ok or stage:return
 stage=1
 window.page.runJavaScript(r'''(async()=>{try{
 const assert=(v,m)=>{if(!v)throw Error(m);};S=seed();S.locks={};IX=null;ensureWorkspace();
 const p=S.projects[0],s=p.systems[0],a=s.acts[0],sp=s.subprofiles[0];a.subs=[sp.id];
 const v=volumeList(p).find(v=>v.s?.id===s.id&&v.sp.id===sp.id),foreign={...v,sp:{id:'FOREIGN',signers:{r4:'FOREIGN-PERSON'}}};
 S.lib.orgs.push({id:'ORG-ONE',full:'Организация исполнителя',inn:'111',address:'Адрес исполнителя'},{id:'ISSUER',full:'Компания выпуска',inn:'222'});
 S.lib.people.push({id:'PERSON-ONE',fio:'Исполнитель Иван Иванович',fioShort:'Исполнитель И. И.',position:'Должность исполнителя',orgId:'ORG-ONE',authority:'Приказ исполнителя'});
 a.signers={r4:'PERSON-ONE'};p.exportIssuer='ISSUER';p.extra=[{k:'Объект',v:'НЕ НАЗВАНИЕ ОБЪЕКТА'}];
 a.num='АР-3.1';a.works='Демонтаж окон';a.place='Все этажи';a.start='2025-09-10';a.end='2025-09-18';a.date='2025-09-18';a.quantityRows=[{id:'zero',name:'Работа',unit:'м²',qty:0,place:'Этаж 1'}];
 let c=wordContext(p,foreign,'a'+a.id),g=t=>c.values[t];
 assert(g('Объект.Наименование')===p.name&&g('ДопПоля.Объект')==='НЕ НАЗВАНИЕ ОБЪЕКТА','Custom field overwrote system field');
 assert(g('Комплект.Компания.Наименование')==='Компания выпуска','Issuer missing');
 assert(g('Подписанты.ИсполнительРабот.Организация.Наименование')==='Организация исполнителя','Issuer leaked into signer');
 assert(g('Подписанты.ИсполнительРабот.Организация.ИНН')==='111'&&g('Подписанты.ИсполнительРабот.ФИО')==='Исполнитель Иван Иванович','Signer fields mixed');
 assert(g('АОСР.Дата.Прописью')==='18 сентября 2025 г.'&&g('АОСР.Дата.День')==='18','Date formats');
 assert(c.collections.Объемы[0].Количество==='0','Zero lost');
 assert(!Object.hasOwn(c.values,'Объект')&&!knownTags().has('ФИО_Прораб'),'Legacy aliases exposed');
 assert(c.bindings.find(x=>x.tag==='Подписанты.ИсполнительРабот.ФИО').source.includes('АР-3.1'),'Binding source missing');
 let rejected=false;try{validateDocumentContext(c,['Объект']);}catch(e){rejected=true;}assert(rejected,'Legacy tag accepted');
 const k=s.aik[0];k.qty=0;k.date='2025-10-01';c=wordContext(p,v,'k'+k.id);assert(c.values['АИК.Количество']===0&&c.values['АОСР.Номер']===''&&c.values['АИК.Номер']===k.num,'AIK and AOSR mixed');
 // Explicit choice among multiple assigned profiles; unrelated profiles must never win.
 const second={...structuredClone(sp),id:'SECOND',signers:{r0:'PERSON-ONE'}};s.subprofiles.push(second);a.subs=[sp.id,second.id];
 c=wordContext(p,{...v,sp:second},'a'+a.id);assert(c.values['Подписанты.СтройконтрольЗаказчика.ФИО']==='Исполнитель Иван Иванович','Selected assigned profile ignored');
 c=wordContext(p,foreign,'a'+a.id);assert(c.issues.some(x=>x.message.includes('комплект подписантов')),'Ambiguous profile silently selected');a.subs=[sp.id];
 a.date='2025-02-31';c=wordContext(p,v,'a'+a.id);assert(c.issues.some(x=>x.tag==='АОСР.Дата'),'Invalid date accepted');a.date='2025-09-18';
 const saved=S.lib.people.find(x=>x.id==='PERSON-ONE');S.lib.people=S.lib.people.filter(x=>x!==saved);c=wordContext(p,v,'a'+a.id);assert(c.issues.some(x=>x.message.includes('подписант удалён')),'Deleted person silently blank');S.lib.people.push(saved);
 a.schemes=[{id:'TEST-SCHEME',name:'Схема',num:'АР-3.1',pages:2,sheetPlaces:{'1':'Этаж 1','2':'Этаж 2'}}];a.tests=[];a.testLinks=[];a.schemeLinks=[];
 c=wordContext(p,v,'cTEST-SCHEME');assert(c.values['АОСР.Номер']==='АР-3.1','Owned scheme lost act');
 const cfg=drawingContext(p,s,{id:'TEST-SCHEME',record:a.schemes[0],owner:a,name:'Схема'},v,a);
 assert(drawingSheetCaption(cfg,2).includes('Этаж 2')&&!drawingSheetCaption(cfg,2).includes('Все этажи'),'Sheet location inheritance');
 c=wordContext(p,v,'a'+a.id);assert(!c.values['АОСР.ПодтверждающиеДокументы'].includes('Ведомость')&&c.values['АОСР.Приложения'].includes('Ведомость'),'Evidence and attachments mixed');
 assert(c.values['Подписанты.СтройконтрольЗаказчика.ФамилияИнициалы']===wordContext(p,foreign,'a'+a.id).values['Подписанты.СтройконтрольЗаказчика.ФамилияИнициалы'],'Foreign profile contamination');
 const html=aosrHtml(a,p,s,sp);assert(html.includes('Организация исполнителя')&&!html.includes('Компания выпуска'),'HTML role mismatch');
 p.participantOrgs={Генподрядчик:'ORG-ONE'};assert(wordContext(p,v,'title').values['Участники.Генподрядчик.ИНН']==='111','Participant ID ignored');
 S.ui.wordObject=p.id;S.ui.tagVolume=v.key;S.ui.tagAct=a.id;
 const routes=['#/home','#/p/'+p.id+'/general','#/p/'+p.id+'/check','#/s/'+s.id+'/params','#/s/'+s.id+'/schemes','#/a/'+a.id+'/main','#/a/'+a.id+'/prev','#/a/'+a.id+'/quantity','#/lib/tags','#/lib/templates','#/lib/profiles','#/build/'+p.id];
 for(const route of routes){history.replaceState(null,'',route);manualAcceptedHash=route;render();assert(document.querySelector('#content').textContent.trim(),'Empty screen '+route);}
 history.replaceState(null,'','#/lib/tags');render();assert(document.querySelector('#content').textContent.includes('Источник'),'Binding screen missing');
 save();await desktopFlush(true);history.replaceState(null,'','#/lib/tags');render();await new Promise(resolve=>setTimeout(resolve,300));window.tagsResult={ok:true,context:wordContext(p,v,'a'+a.id),screens:routes.length};
 }catch(e){window.tagsResult={error:e.stack};}})();''')
def receive(value):
 global stage
 if not value or stage!=1:return
 result=json.loads(value)
 if result.get('error'):fail(result['error']);return
 try:
  assert not window.page.console_errors,window.page.console_errors
  from word_templates import sample_docx,fill_docx,inspect_docx
  c=result['context'];source=sample_docx('aosr','АОСР',Path(tmp.name)/'source.docx')
  out=fill_docx(source.read_bytes(),Path(tmp.name)/'filled.docx',c['values'],c['collections'])
  assert not inspect_docx(out.read_bytes())['tags']
  Path('validation').mkdir(exist_ok=True);window.grab().save(str(Path('validation/tags-ui.png').resolve()))
  stage=2;timer.stop();print('PASS: canonical tag isolation, role bundles, date parts, zero, obsolete tags, binding report, 12 screens and filled AOSR DOCX');app.quit()
 except Exception as e:fail(e)
def poll():
 if stage==0:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.tagsResult?JSON.stringify(window.tagsResult):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Tag acceptance timed out'))
code=app.exec();dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
