"""Real Qt WebEngine integration check, separate from fast unit tests."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS', '') + ' --disable-ipc-flooding-protection'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPdfWriter
from app import Window, dispose_window
from storage import Store

application = QApplication([])
temp = tempfile.TemporaryDirectory()
store = Store(Path(temp.name) / 'database')
window = Window(store, test_profile=True)
assert window.profile.isOffTheRecord()
window.show()
stage = 0
errors = []


def fail(message):
    errors.append(message)
    application.exit(1)


def verify_result(result):
    global stage
    if stage != 1:
        return
    try:
        value = json.loads(result)
        if value.get('error'):
            fail(value['error'])
            return
        assert value['projects'] == 3, value
        assert not value['failed'], value
        assert not window.page.console_errors, window.page.console_errors
        assert store.load()['state']['meta']['name'] == 'Qt integration test'
        assert store.load()['state']['projects'][0]['short'] == 'Сохранено после изменения'
        assert any(b['reason']=='Integration test' for b in store.list_backups())
        stage = 2
        timer.stop()
        print(f"PASS: native QWebChannel, folder startup, {value['count']} contextual views, save queue, PDF import, ZIP checkpoint")
        window.page.runJavaScript("S.meta.name='Сохранено при закрытии';save();window.closeSnapshot=JSON.stringify(S)", lambda _: window.close())
    except Exception as e:
        fail(str(e))


def ready(value):
    global stage
    if not value or stage:
        return
    stage = 1
    pdf = Path(temp.name) / 'две страницы.pdf'
    writer = QPdfWriter(str(pdf))
    painter = QPainter(writer)
    painter.drawText(30, 100, 'First page')
    writer.newPage()
    painter.drawText(30, 100, 'Second page')
    painter.end()
    del painter, writer
    with patch('app.QFileDialog.getOpenFileName', return_value=(str(pdf), 'PDF')):
        imported = json.loads(window.bridge.request('pickPdf', '{}'))
    if not imported['ok'] or imported['value']['pages'] != 2:
        fail('Native PDF import failed: ' + str(imported))
        return
    assert store.asset_path(imported['value']['id'])[0].read_bytes() == pdf.read_bytes()
    window.grab().save(str(Path(__file__).resolve().parents[1] / 'qt-preview.png'))
    script = '''(async()=>{try{
      if(S.projects.length!==0)throw Error('First launch must create an empty workspace');
      A.newProject();document.querySelector('#np-n').value='Новый реальный объект';MB[1].f();
      const project=S.projects[0];A.newSystem({p:project.id});document.querySelector('input[name=ns][value="ВК"]').checked=true;MB[1].f();
      const system=project.systems[0];A.newAct({s:system.id});MB[1].f();await desktopFlush(true);
      const stored=await nativeCall('load');
      if(stored.state.projects[0].systems[0].acts.length!==1)throw Error('New object/system/act workflow not persisted');
      S=seed();S.locks={};S.meta.name='Qt integration test';ensureWorkspace();save();
      S.projects[0].short='Сохранено после изменения';save();await desktopFlush(true);
      await desktopFlush(true);S.projects[0].short='Сохранено после изменения';save();await desktopFlush(true);
      await backup('Integration test');
      // Exercise the actual polling function with a local edit arriving before its reply.
      const realCall=nativeCall;
      nativeCall=async(op,params)=>{const result=await realCall(op,params);if(op==='poll'){S.meta.name='Изменено во время обновления';save();}return result;};
      try{await desktopPollFolder();}finally{nativeCall=realCall;}
      if(S.meta.name!=='Изменено во время обновления')throw Error('Delayed folder reply overwrote local edit');
      await desktopFlush(true);
      if((await nativeCall('load')).state.meta.name!=='Изменено во время обновления')throw Error('Concurrent edit not persisted');
      S.meta.name='Qt integration test';save();await desktopFlush(true);
      const routes=['#/sync','#/lib/orgs','#/lib/templates','#/lib/tags','#/lib/profiles','#/home','#/settings/general','#/settings/backups','#/settings/history','#/settings/trash'];
      for(const p of S.projects){
        for(const t of ['overview','general','info','mats','admin','surveys','operations','ozhr','check'])routes.push('#/p/'+p.id+'/'+t);
        routes.push('#/build/'+p.id);
        for(const s of p.systems){
          for(const t of ['overview','acts','schemes','scheme','materials','aik','trials','jr','subs','params'])routes.push('#/s/'+s.id+'/'+t);
          for(const a of s.acts)for(const t of ['main','mat','schemes','tests','photos','scan','prev'])routes.push('#/a/'+a.id+'/'+t);
        }
      }
      const failed=[];for(const r of routes){history.replaceState(null,'',r);render();if(document.querySelector('#content').innerText.includes('Ошибка отображения'))failed.push(r);}
      location.hash='#/home';render();await desktopFlush(true);
      window.smokeResult=JSON.stringify({projects:S.projects.length,failed,count:routes.length});
    }catch(e){window.smokeResult=JSON.stringify({error:e.stack});}})();'''
    window.page.runJavaScript(script)


def poll():
    if not stage:
        window.page.runJavaScript('window.desktopReady===true', ready)
    else:
        window.page.runJavaScript('window.smokeResult||null', lambda value: verify_result(value) if value else None)


timer = QTimer()
timer.timeout.connect(poll)
timer.start(250)
QTimer.singleShot(40000, lambda: fail('Qt integration timeout'))
code = application.exec()
dispose_window(window)
if not code:
    actual=store.load()['state']['meta']['name']
    assert actual == 'Сохранено при закрытии', f'Close flush lost pending state: {actual!r}'
    print('PASS: closing window flushes pending folder changes')
store.close()
assert not (Path(temp.name) / 'database/webprofile').exists()
assert not (Path(temp.name) / 'database/webcache').exists()
temp.cleanup()
if errors:
    print('\n'.join(errors), file=sys.stderr)
sys.exit(code)
