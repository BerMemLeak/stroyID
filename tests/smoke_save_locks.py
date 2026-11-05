"""Real UI saves and closing while Windows sharing violations are injected."""
import sys,tempfile,json,traceback,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app import Window,dispose_window
from folder_store import Store
app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);store=Store(root/'database');window=Window(store,test_profile=True);window.show();stage=0;errors=[];counts={};faults=0;real_replace=os.replace

def sharing_replace(source,destination):
 global faults
 target=Path(destination)
 if target.suffix=='.json' and 'История' in target.parts:
  key=str(target);n=counts.get(key,0);counts[key]=n+1
  if n<2:
   faults+=1;e=PermissionError(13,'Проверочная краткая блокировка истории');e.winerror=5;raise e
 return real_replace(source,destination)
def fail(error):errors.append(str(error));app.exit(1)
def ready(v):
 global stage
 if stage or not v:return
 stage=1
 window.page.runJavaScript('''(async()=>{try{
 for(let n=0;n<10;n++){S.meta.name='Сохранение '+n;logH('Проверочная запись '+n);save();await desktopFlush(true);if(desktopDirty||desktopError)throw Error('Save did not finish');}
 window.lockedSaveResult={ok:true};
 }catch(e){window.lockedSaveResult={error:e.stack};}})();''')
def received(raw):
 global stage
 if stage!=1 or not raw or raw=='null':return
 value=json.loads(raw)
 if value.get('error'):fail(value['error']);return
 try:
  assert not window.bridge.watcher.files(),'Native watcher still holds target file subscriptions'
  assert not window.page.console_errors,window.page.console_errors
  stage=2;timer.stop();window.page.runJavaScript("S.meta.name='Сохранено при закрытии с блокировкой';logH('Проверка закрытия с блокировкой');save()",lambda _:window.close())
 except Exception:fail(traceback.format_exc())
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady',ready)
 elif stage==1:window.page.runJavaScript('window.lockedSaveResult?JSON.stringify(window.lockedSaveResult):null',received)
timer=QTimer();timer.timeout.connect(poll);timer.start(150);QTimer.singleShot(90000,lambda:fail('Save/lock UI timed out'))
with patch('folder_core.os.replace',side_effect=sharing_replace):code=app.exec()
dispose_window(window)
try:
 if code==0:
  assert stage==2;assert faults>=22,(faults,counts)
  loaded=Store(store.root).load();assert loaded['state']['meta']['name']=='Сохранено при закрытии с блокировкой';assert not loaded['warnings'];assert not loaded['conflicts'];assert not list(root.rglob('.sid-*.tmp'))
  print('PASS: 10 explicit saves and automatic close with',faults,'injected WinError 5 failures; directory-only watcher; reopen without loss or conflicts')
except Exception:errors.append(traceback.format_exc());code=1
store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
