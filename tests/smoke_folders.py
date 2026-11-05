"""Working interface: organization ownership, export profiles and folder/JSON recovery."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPdfWriter,QPainter
from app import Window,dispose_window
from storage import Store
app=QApplication([]);tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);store=Store(root/'base');window=Window(store,test_profile=True);window.show();stage=0;errors=[]
def fail(x):errors.append(str(x));app.exit(1)
def ready(v):
 global stage
 if not v or stage:return
 stage=1
 window.page.runJavaScript('''(async()=>{try{
 S=seed();S.projects=S.projects.slice(0,1);S.lib.base=S.lib.base.slice(0,1);S.locks={};save();await desktopFlush(true);
 const p=S.projects[0],pf=S.lib.profiles[0],o=S.lib.orgs[0];
 history.replaceState(null,'','#/lib/orgs/'+o.id);render();
 if(document.querySelector('#content').innerText.includes('Матрица подписантов'))throw Error('Old organization tabs remain');
 A.orgPerson({id:o.id});if(S.lib.people.at(-1).orgId!==o.id)throw Error('Representative owner');
 A.orgOrder({id:o.id});if(S.lib.orders.at(-1).orgId!==o.id)throw Error('Order owner');
 history.replaceState(null,'','#/lib/profiles/'+pf.id);render();
 if(!document.querySelector('#content').innerText.includes('Настройки экспорта'))throw Error('Export settings missing');
 pf.exportSettings={order:['reg','title','aosr','schemes'],off:['quality']};p.exportMode='profile';p.exportProfile=pf.id;
 const v=volumeList(p).find(v=>v.kind==='T2'),b=blocksFor(p,v);
 if(b[0].key!=='reg'||!b.find(x=>x.key==='quality')?.off)throw Error('Profile settings not applied');
 p.exportMode='custom';const b2=blocksFor(p,v);if(b2[0].key!=='title'||b2.find(x=>x.key==='quality')?.off)throw Error('Custom settings overwritten');
 history.replaceState(null,'','#/lib/tags');render();if(document.querySelector('#content').innerText.includes('Пример значений'))throw Error('Tag examples remain');
 if(document.querySelector('#top [data-a="menu"],#top [data-a="exportJson"],#top [data-h^="#/build"],#tree a[href="#/import"]'))throw Error('Removed UI remains');
 save();await desktopFlush(true);window.folderStage=1;
 }catch(e){window.folderResult={error:e.stack};}})();''')
def receive(v):
 global stage
 if not v:return
 v=json.loads(v)
 if v.get('error'):fail(v);return
 if stage==1:
  key='base:'+store.load()['state']['lib']['base'][0]['id'];path=store.path(store.paths[key]);path.write_text('{ broken')
  pdf=path.parent/'Сертификат из Проводника.pdf';w=QPdfWriter(str(pdf));p=QPainter(w);p.drawText(20,100,'Certificate');p.end();del p,w;stage=2
  window.page.runJavaScript('''(async()=>{try{await A.folderRefresh();if(!folderWarnings.some(w=>w.message.includes('Повреждён JSON')))throw Error('JSON warning missing');history.replaceState(null,'','#/sync');render();window.folderStage=2;}catch(e){window.folderResult={error:e.stack};}})();''')
 elif stage==2:
  window.grab().save(str(Path(__file__).resolve().parents[1]/'validation'/'sync.png'));key=next(w['key'] for w in store.warnings if w.get('key'));stage=3
  script='''(async()=>{try{await A.folderRepair({key:KEY});const label=[...document.querySelectorAll('.dlg label')].find(x=>x.textContent.includes('Производитель'));if(!label)throw Error('Repair form missing');label.querySelector('input').value='Исправлено инженером';MB[1].f();closeModal();await A.folderRefresh();if(folderWarnings.length)throw Error(JSON.stringify(folderWarnings));const m=S.lib.base.find(m=>m.maker==='Исправлено инженером');if(!m.docs.some(d=>d.file==='Сертификат из Проводника.pdf'))throw Error('Explorer PDF not found');history.replaceState(null,'','#/lib/orgs/'+S.lib.orgs[0].id);render();window.folderStage=3;}catch(e){window.folderResult={error:e.stack};}})();'''.replace('KEY',json.dumps(key));window.page.runJavaScript(script)
 elif stage==3:
  window.grab().save(str(Path(__file__).resolve().parents[1]/'validation'/'organizations.png'));stage=4
  window.page.runJavaScript("history.replaceState(null,'','#/lib/profiles/'+S.lib.profiles[0].id);render();document.querySelector('#content').scrollTop=0;window.folderStage=4")
 elif stage==4:
  window.grab().save(str(Path(__file__).resolve().parents[1]/'validation'/'profiles.png'));print('PASS: organization ownership, profile/custom export, clean navigation, JSON repair form, Explorer PDF discovery');app.exit(0)
def poll():
 if not stage:window.page.runJavaScript('window.desktopReady',ready)
 else:window.page.runJavaScript('JSON.stringify(window.folderResult||((window.folderStage==='+str(stage)+')?{ok:true}:null))',lambda v:receive(v) if v and v!='null' else None)
(Path(__file__).resolve().parents[1]/'validation').mkdir(exist_ok=True)
timer=QTimer();timer.timeout.connect(poll);timer.start(200);QTimer.singleShot(60000,lambda:fail('timeout'));code=app.exec();dispose_window(window);store.close();tmp.cleanup();print('\n'.join(errors));sys.exit(code)
