"""Exercise organization role selection with real pointer/keyboard events in WebEngine."""
import json,sys,tempfile,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEventLoop,QPoint,QTimer,Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from app import Window,dispose_window
from folder_store import Store
app=QApplication([]);tmp=tempfile.TemporaryDirectory();store=Store(Path(tmp.name)/'database')
window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(error):errors.append(str(error));app.exit(1)
def js(script):
 result=[];loop=QEventLoop();timer=QTimer();timer.setSingleShot(True)
 timer.timeout.connect(loop.quit);timer.start(10000)
 window.page.runJavaScript(script,lambda value:(result.append(value),loop.quit()))
 loop.exec();timer.stop()
 if not result:raise AssertionError('JavaScript callback timed out')
 return result[0]
def wait_js(script):
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if js(script):return True
  QTest.qWait(20)
 return False
def point(selector):
 data=json.loads(js("JSON.stringify((()=>{const el=document.querySelector("+json.dumps(selector)+");if(!el)throw Error('Missing role control');el.scrollIntoView({block:'nearest'});const r=el.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})())"))
 return QPoint(round(data['x']),round(data['y']))
def click(selector):QTest.mouseClick(window.view.focusProxy(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(selector));QTest.qWait(80)
def key(code):QTest.keyClick(window.view.focusProxy(),code);QTest.qWait(80)
def exercise():
 global stage
 try:
  trigger='[data-a="orgRoleOpen"][data-id="o1"]'
  click(trigger)
  assert wait_js("!document.querySelector('.org-role-list').hidden"),'Pointer click did not open role choices'
  assert wait_js("document.querySelectorAll('.org-role-list [role=option]').length===ORG_ROLES.length"),'Role options missing'
  screenshot=Path('validation/org-role-picker.png');screenshot.parent.mkdir(exist_ok=True);window.grab().save(str(screenshot.resolve()))
  click('[data-role-value="Технический заказчик"]')
  assert wait_js("org('o1').role==='Технический заказчик'&&document.querySelector('.org-role-list').hidden"),'Pointer selection failed'
  assert wait_js("document.activeElement===document.querySelector('[data-a=orgRoleOpen]')"),'Selection did not restore focus'
  key(Qt.Key.Key_Space);assert wait_js("!document.querySelector('.org-role-list').hidden"),'Keyboard open failed'
  key(Qt.Key.Key_Down);key(Qt.Key.Key_Return)
  assert wait_js("org('o1').role==='Генеральный подрядчик'"),'Keyboard selection failed'
  key(Qt.Key.Key_Space);key(Qt.Key.Key_Down);key(Qt.Key.Key_Escape)
  assert wait_js("org('o1').role==='Генеральный подрядчик'&&document.querySelector('.org-role-list').hidden"),'Escape changed role'
  click(trigger);click('[data-ent="org"][data-id="o1"][data-f="inn"]')
  assert wait_js("document.querySelector('.org-role-list').hidden"),'Outside click did not close menu'
  js("S.ui.ro=true;render()")
  assert wait_js("document.querySelector('[data-a=orgRoleOpen]').disabled"),'Readonly role button is enabled'
  click(trigger);assert wait_js("document.querySelector('.org-role-list').hidden"),'Readonly menu opened'
  js("S.ui.ro=false;render();(async()=>{try{await desktopFlush(true);const saved=await nativeCall('load');window.rolePersisted=saved.state.lib.orgs.find(o=>o.id==='o1').role==='Генеральный подрядчик'&&saved.state.lib.orgs.find(o=>o.id==='o2').role==='Подрядчик';}catch(e){window.roleFailure=e.stack;}})()")
  stage=2
 except Exception:fail(traceback.format_exc())
def poll():
 global stage
 try:
  if stage==0 and js('window.desktopReady===true'):
   stage=1
   js("S=seed();S.projects=[];S.locks={};S.lib.orgs=S.lib.orgs.slice(0,2);Object.assign(org('o1'),{full:'Общество с ограниченной ответственностью УЛЬТРА ТЕХНОЛОГИИ',short:'',role:'Подрядчик'});org('o2').role='Подрядчик';history.replaceState(null,'','#/lib/orgs/o1');manualAcceptedHash=location.hash;render()")
   QTimer.singleShot(100,exercise)
  elif stage==2:
   error=js('window.roleFailure||null')
   if error:raise AssertionError(error)
   if js('window.rolePersisted===true'):
    assert not window.page.console_errors,window.page.console_errors
    stage=3;timer.stop();print('PASS: actual pointer opening/selection, keyboard opening/selection, Escape, outside click, readonly, save/reload, organization isolation');window.close()
 except Exception:fail(traceback.format_exc())
timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(60000,lambda:fail('Organization role picker timed out'))
code=app.exec();dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
