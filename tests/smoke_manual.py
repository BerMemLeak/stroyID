"""Auto-save, cancelled creation, saved navigation, scoped documents and event-driven idle checks."""
import json,sys,tempfile,time,traceback,io
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from pypdf import PdfWriter
from app import Window,dispose_window
from folder_store import Store
app=QApplication([]);temp=tempfile.TemporaryDirectory();root=Path(temp.name);store=Store(root/'data')
for name,width in [('private.pdf',600),('common.pdf',700)]:
 w=PdfWriter();w.add_blank_page(width,800);w.write(root/name)
window=Window(store,test_profile=True);window.show();stage=0;errors=[];result={};idle={};cpu={};heartbeat=0

def fail(message):errors.append(str(message));app.exit(1)
def ready(value):
 global stage
 if not value or stage:return
 stage=1
 script=r'''(async()=>{try{
 const clickCreate=()=>document.querySelector('[data-mb="1"]').click();
 const auditOrg={id:'o-audit',full:'',short:'Новая организация',role:'Подрядчик',inn:'',ogrn:'',address:'',sro:'',props:'',logo:''};S.lib.orgs.push(auditOrg);save();await desktopFlush(true);
 history.replaceState(null,'','#/lib/orgs/'+auditOrg.id);manualAcceptedHash=location.hash;render();const orgInput=document.querySelector('[data-ent="org"][data-f="short"]'),historyBefore=JSON.stringify(S.history),auditName='Ремстрой';
 for(let i=1;i<=auditName.length;i++){orgInput.value=auditName.slice(0,i);orgInput.dispatchEvent(new Event('input',{bubbles:true}));}
 const fullInput=document.querySelector('[data-ent="org"][data-f="full"]');fullInput.value='ООО Ремстрой';fullInput.dispatchEvent(new Event('input',{bubbles:true}));
 if(JSON.stringify(S.history)!==historyBefore)throw Error('History records draft letters');await new Promise(r=>setTimeout(r,250));const orgStored=await nativeCall('load');if(orgStored.state.lib.orgs[0].short!=='Новая организация'||JSON.stringify(orgStored.state.history)!==historyBefore)throw Error('Draft organization or history persisted');
 await A.desktopSave();const auditEntries=S.history.filter(x=>x.text.startsWith('Изменён(а) организация'));if(auditEntries.length!==1||!auditEntries[0].text.includes('Ремстрой'))throw Error('Expected one final organization history event: '+JSON.stringify(auditEntries));
 const savedHistory=JSON.stringify(S.history);const discardInput=document.querySelector('[data-ent="org"][data-f="short"]');discardInput.value='Отменённое имя';discardInput.dispatchEvent(new Event('input',{bubbles:true}));manualDiscard();if(JSON.stringify(S.history)!==savedHistory||manualAuditEdits.size)throw Error('Discard kept draft history');await A.desktopSave();if(JSON.stringify(S.history)!==savedHistory)throw Error('Discarded history reappeared');

 A.newProject();document.querySelector('#np-n').value='Объект один';document.querySelector('#np-a').value='Адрес из объекта';clickCreate();await desktopFlush(true);const p=S.projects[0];
 A.newSystem({p:p.id});document.querySelector('input[name=ns][value="ВК"]').checked=true;clickCreate();await desktopFlush(true);const s=p.systems[0];
 A.newAct({s:s.id});if(s.acts.length)throw Error('Draft act inserted before Create');document.querySelector('#create-act-works').value='Первичные работы';clickCreate();await desktopFlush(true);const a=s.acts[0];history.replaceState(null,'','#/a/'+a.id);manualAcceptedHash=location.hash;render();
 if(document.querySelector('#content [data-ent="act"][data-f="place"]'))throw Error('Manual place input remains');if(document.querySelector('#content').innerText.includes('Как в комплекта'))throw Error('Signer grammar remains');if(!window.desktopReady)throw Error('Channel not ready');
 if(document.querySelectorAll('#tree a[href^="#/s/'+s.id+'/"]').length)throw Error('Duplicate sidebar sections remain');
 const tree=document.querySelector('#tree .tn'),top=document.querySelector('#top input');let input=document.querySelector('[data-ent="act"][data-f="works"]');for(let i=0;i<30;i++){input.value='Несохранённый ввод '+i;input.dispatchEvent(new Event('input',{bubbles:true}));}
 if(tree!==document.querySelector('#tree .tn')||top!==document.querySelector('#top input'))throw Error('Typing rebuilt navigation');await new Promise(r=>setTimeout(r,1300));const stored=await nativeCall('load');if(stored.state.projects[0].systems[0].acts[0].works!=='Несохранённый ввод 29')throw Error('Automatic save missing');
 go('#/lib/base');await new Promise(r=>setTimeout(r,200));if(document.querySelector('.dlg')||location.hash!=='#/lib/base')throw Error('Saved navigation blocked');
 history.replaceState(null,'','#/a/'+a.id);manualAcceptedHash=location.hash;render();input=document.querySelector('[data-ent="act"][data-f="works"]');input.value='Сохранено кнопкой';input.dispatchEvent(new Event('input',{bubbles:true}));await A.desktopSave();if(desktopDirty)throw Error('Explicit save left dirty state');
 A.newMat({p:p.id});document.querySelector('#new-material-name').value='Незавершённый материал';window.dispatchEvent(new Event('blur'));document.dispatchEvent(new Event('visibilitychange'));await new Promise(r=>setTimeout(r,500));if(p.materials.length||S.lib.base.length)throw Error('Alt-Tab created material');closeModal();
 A.newMat({p:p.id});document.querySelector('#new-material-name').value='Свой материал';clickCreate();await desktopFlush(true);const own=p.materials[0];if(own.baseId||S.lib.base.length)throw Error('Own material became global');A.rowAdd({ent:'mat',id:own.id,p:'docs',k:'doc'});own.docs[0].type='Паспорт';await A.pickPdf({ent:'mat',id:own.id,p:'docs.#'+own.docs[0].id});await A.desktopSave();if(!own.docs[0].fileKey.startsWith('Объект один/'))throw Error('Object passport is outside object');
 A.libNew({k:'base'});document.querySelector('#new-material-name').value='Общий стандартный материал';clickCreate();await desktopFlush(true);const common=S.lib.base[0];A.rowAdd({ent:'base',id:common.id,p:'docs',k:'doc'});common.docs[0].type='Паспорт';await A.pickPdf({ent:'base',id:common.id,p:'docs.#'+common.docs[0].id});await A.desktopSave();
 A.baseToProj({id:common.id});document.querySelector('.dlg input[type="checkbox"]').checked=true;clickCreate();await A.desktopSave();
 A.newProject();document.querySelector('#np-n').value='Объект два';clickCreate();await desktopFlush(true);const p2=S.projects[1];A.baseToProj({id:common.id});document.querySelector('.dlg input[value="'+p2.id+'"]').checked=true;clickCreate();await A.desktopSave();if(p2.materials.some(m=>m.docs.length)||p2.materials.length!==1)throw Error('Global passport copied into object');
 const linked=p.materials.find(m=>m.baseId);history.replaceState(null,'','#/m/'+linked.id);manualAcceptedHash=location.hash;render();const maker=document.querySelector('[data-ent="base"][data-f="maker"]');if(!maker)throw Error('Shared material cannot be edited from object');maker.value='Общий завод';maker.dispatchEvent(new Event('input',{bubbles:true}));await A.desktopSave();if(mF(p2.materials[0],'maker')!=='Общий завод'||document.querySelector('.dlg'))throw Error('Global editing is not shared or displays confirmation');
 a.place='Старое ручное место';if(!aosrHtml(a,p,s,s.subprofiles[0]).includes(p.address)||wordContext(p,volumeList(p).find(v=>v.s?.id===s.id),'a'+a.id).values.Место_Работ!==p.address)throw Error('Object place not substituted into HTML/Word');save();await desktopFlush(true);
 S.meta.passportReviewPending=true;history.replaceState(null,'','#/lib/base');manualAcceptedHash=location.hash;render();if(!document.querySelector('[data-passport-review]'))throw Error('Migration review missing');A.passportReview();await A.desktopSave();
 history.replaceState(null,'','#/a/'+a.id);manualAcceptedHash=location.hash;render();window.manualResult={ok:true,pid:p.id,aid:a.id,own:own.id,common:common.id,p2:p2.id};
 }catch(e){window.manualResult={error:e.stack};}})();'''
 window.page.runJavaScript(script)

def cpu_total():return time.process_time()

def settled():
 global idle,cpu
 idle=store.metrics.copy();cpu={'start':time.perf_counter(),'cpu':cpu_total()};QTimer.singleShot(7000,finish_idle)

def finish_idle():
 global stage
 try:
  elapsed=time.perf_counter()-cpu['start'];usage=100*(cpu_total()-cpu['cpu'])/elapsed
  assert store.metrics['loads']==idle['loads'],(idle,store.metrics)
  assert store.metrics['saves']==idle['saves'],(idle,store.metrics)
  assert store.metrics['hashed_files']==idle['hashed_files'],(idle,store.metrics)
  assert usage<10,usage
  report={'version':'0.9.4','idle_seconds':round(elapsed,3),'main_process_cpu_percent_one_core':round(usage,3),'idle_storage_loads':0,'idle_storage_saves':0,'idle_document_hashes':0,'debounced_auto_save':True,'typing_no_navigation_rebuild':True,'history_one_final_card_event':True,'discard_removes_pending_history':True,'object_and_common_scope':True}
  Path('validation').mkdir(exist_ok=True);Path('validation/manual-and-idle.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');window.grab().save(str(root/'manual-ui.png'))
  print('PASS: debounced auto-save, no per-letter persistence/chrome rebuild, cancelled Alt-Tab draft, prompt-free saved navigation, private/common passports and shared edits, automatic HTML/Word address, icon, migration review; idle CPU',round(usage,3),'%, zero storage refreshes/hashes')
  # Closing is the only automatic commit: keep this edit deliberately unsaved.
  stage=3
  global original_save
  original_save=store.save
  def rejected(*args,**kwargs):raise OSError('Проверочный отказ сохранения')
  store.save=rejected
  window.page.runJavaScript("S.meta.name='Автосохранено при закрытии';const e=document.createElement('input');Object.assign(e.dataset,{ent:'org',id:'o-audit',f:'short'});e.value='Компания при закрытии';apply(e,true);save()",lambda _:window.close())
  QTimer.singleShot(1000,check_failed_close)
 except Exception:fail(traceback.format_exc())

def check_failed_close():
 global stage
 try:
  assert window.isVisible() and not window.allow_close and not window.closing
  def receive_state(value):
   global stage
   try:
    assert value is True,'Failed close lost entered data'
    store.save=original_save;stage=4;print('PASS: failed exit save keeps window and unsaved data; retry succeeds');window.close()
   except Exception:fail(traceback.format_exc())
  window.page.runJavaScript("S.meta.name==='Автосохранено при закрытии'&&desktopDirty&&desktopError.includes('Проверочный отказ')&&manualAuditEdits.size===1&&!S.history.some(h=>h.text.includes('Компания при закрытии'))",receive_state)
 except Exception:fail(traceback.format_exc())

def receive(value):
 global stage,result
 if stage!=1 or not value or value=='null':return
 result=json.loads(value)
 if result.get('error'):fail(result);return
 try:
  assert not window.page.console_errors,window.page.console_errors
  assert not window.windowIcon().isNull()
  current=store.load()['state'];p=current['projects'][0];assert p['systems'][0]['acts'][0]['works']=='Сохранено кнопкой';assert len(current['lib']['base'])==1;assert not list((store.root/'Объект два').rglob('*.pdf'));assert len([f for f in (store.root/'Справочники').rglob('*.pdf') if 'История версий' not in f.parts])==1
  stage=2;timer.stop();QTimer.singleShot(800,settled)
 except Exception:fail(traceback.format_exc())

def poll():
 if stage==0:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('JSON.stringify(window.manualResult||null)',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(90000,lambda:fail('Manual UI timed out'))
with patch('app.QMessageBox.warning',return_value=None),patch('app.QFileDialog.getOpenFileName',side_effect=[(str(root/'private.pdf'),'PDF'),(str(root/'common.pdf'),'PDF')]):code=app.exec()
dispose_window(window)
if code==0:
 reopened=Store(store.root).load()['state'];assert reopened['meta']['name']=='Автосохранено при закрытии';assert len([h for h in reopened['history'] if 'Компания при закрытии' in h['text']])==1;print('PASS: automatic exit save and reopen; one final history event after failed save and retry')
store.close();temp.cleanup();print('\n'.join(errors));sys.exit(code)
