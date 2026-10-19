"""Real card-history UI: three peers, locked editing, preview, rollback and pruning."""
import copy,json,shutil,sys,tempfile,traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app import Window,dispose_window
from folder_store import Store
from test_storage import state,material
app=QApplication.instance() or QApplication([]);temp=tempfile.TemporaryDirectory();root=Path(temp.name)
store=Store(root/'base');s=state();s['lib']['base']=[material('m','Труба')];store.save(s,0)
from pypdf import PdfWriter
source=root/'Паспорт.pdf';writer=PdfWriter();writer.add_blank_page(595,842);writer.write(source);writer.close();original_pdf=source.read_bytes()
s=store.load()['state'];asset=store.import_file(source);s['lib']['base'][0]['docs']=[{'id':'doc','type':'Паспорт','num':'1','date':'2026-10-19','file':asset['name'],'fileKey':asset['id']}];store.save(s,store.revision)
peers=[]
for n in range(3):
 path=root/('peer'+str(n));shutil.copytree(store.root,path);peer=Store(path);peer.actor='ПК-'+str(n)
 s=peer.load()['state'];s['lib']['base'][0]['maker']='Вариант '+str(n);peer.save(s,peer.revision);peers.append(peer)
for peer in peers:
 for file in peer.events_dir.glob('*.json'):shutil.copy2(file,store.events_dir/file.name)
store.load();assert len(store.conflicts[0]['versions'])==3
window=Window(store,test_profile=True);window.resize(1500,1000);window.show();stage=0;errors=[];opened=[]
def fail(e):errors.append(str(e));app.exit(1)
def ready(ok):
 global stage
 if stage or not ok:return
 stage=1
 script=r'''(async()=>{try{
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
 go('#/lib/base/m');render();
 assert(document.querySelector('[data-history-locked]'),'Conflict did not lock card');
 assert(document.querySelector('[data-ent="base"][data-f="maker"]')?.disabled,'Conflicting field editable');
 await A.historyOpen({key:'base:m'});render();
 let cache=historyCache.get('base:m');assert(cache.data.conflict&&cache.data.heads.length===3,'Three variants missing');
 assert(document.querySelectorAll('.history-point.current').length===3,'Timeline variants missing');
 const chosen=cache.data.versions.find(v=>v.current);await A.historyView({key:'base:m',version:chosen.id});
 assert(document.querySelector('.history-preview'),'Preview absent');
 const historicalFile=cache.detail.files[0];assert(historicalFile?.ready,'Historical PDF missing');await A.historyFile({key:'base:m',version:chosen.id,sha:historicalFile.sha});
 const savedMaker=S.lib.base[0].maker;
 assert([...document.querySelectorAll('.history-form input,.history-form select,.history-form textarea')].every(x=>x.disabled),'Old version editable');
 assert(S.lib.base[0].maker===savedMaker,'Preview changed live state');
 A.historyRestore({key:'base:m',version:chosen.id});await MB[1].f();closeModal();
 assert(!folderConflicts.length,'Choosing version did not resolve conflict');
 const original=S.lib.base[0].maker,resolution=historyCache.get('base:m').data.versions[0].id;
 const delayed=await nativeCall('poll');
 S.lib.base[0].maker='После выбора';save();await desktopFlush(true);
 const savedHeads=JSON.stringify(desktopSavedHeads);acceptFolder(delayed);
 assert(S.lib.base[0].maker==='После выбора'&&JSON.stringify(desktopSavedHeads)===savedHeads,'Delayed poll rolled back saved card or heads');
 await A.historyRefresh({key:'base:m'});
 const later=historyCache.get('base:m').data.versions[0].id;
 A.historyRestore({key:'base:m',version:resolution});await MB[1].f();closeModal();
 assert(S.lib.base[0].maker===original,'Rollback failed');
 A.historyRestore({key:'base:m',version:later});await MB[1].f();closeModal();
 assert(S.lib.base[0].maker==='После выбора','Return to later version failed');
 cache=historyCache.get('base:m');const old=cache.data.versions.find(v=>!v.current);
 historyChecks.set('base:m',new Set([old.id]));await A.historyDelete({key:'base:m'});await MB[1].f();closeModal();
 assert(!historyCache.get('base:m').data.versions.some(v=>v.id===old.id),'Deleted version still shown');
 window.historySmoke={ok:true,versions:historyCache.get('base:m').data.versions.length};
 }catch(e){window.historySmoke={error:e.stack};}})();'''
 window.page.runJavaScript(script)
def receive(raw):
 global stage
 if stage!=1 or not raw:return
 try:
  result=json.loads(raw);assert result.get('ok'),result
  assert not window.page.console_errors,window.page.console_errors
  assert len(opened)==1 and not opened[0].is_relative_to(store.root),'History file opened in working base'
  opened[0].write_bytes(b'External editor changed the preview copy')
  sha=__import__('hashlib').sha256(original_pdf).hexdigest();assert store._asset_source('base:m',sha).read_bytes()==original_pdf
  stage=2;timer.stop();QTimer.singleShot(250,finish)
 except Exception:fail(traceback.format_exc())
def finish():
  folder=Path(__file__).resolve().parents[1]/'tmp/history';folder.mkdir(parents=True,exist_ok=True);window.grab().save(str(folder/'timeline.png'))
  print('PASS: three conflict variants, edit lock, readonly card preview, choice, rollback/return, timeline and selected-version deletion')
  window.close()
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady===true',ready)
 elif stage==1:window.page.runJavaScript('window.historySmoke?JSON.stringify(window.historySmoke):null',receive)
timer=QTimer();timer.timeout.connect(poll);timer.start(150);QTimer.singleShot(90000,lambda:fail('History UI timed out'))
with patch('app.QDesktopServices.openUrl',side_effect=lambda url:opened.append(Path(url.toLocalFile())) or True):code=app.exec()
timer.stop();dispose_window(window);store.close();temp.cleanup()
for path in opened:
 if path.exists():path.unlink()
if errors:print('\n'.join(errors),file=sys.stderr)
sys.exit(1 if errors or stage!=2 else code)
