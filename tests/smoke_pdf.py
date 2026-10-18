"""Verify the real UI exports forms, photos, selected source sheets and all volumes."""
import base64
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer, QBuffer, QIODevice
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter
from PySide6.QtGui import QImage
from app import Window, dispose_window
from storage import Store
from pdf_export import render_html
from pdf_text import page_text

application = QApplication.instance() or QApplication([])
work = tempfile.TemporaryDirectory()
root = Path(work.name)
store = Store(root / 'data')
writer = PdfWriter()
for n in range(3):
    data = render_html('<h2>ЛИСТ ИСХОДНОЙ СХЕМЫ ' + str(n + 1) + '</h2>', root / f'sheet-{n}.pdf')
    writer.append(PdfReader(io.BytesIO(data)), import_outline=False)
writer.write(root / 'source.pdf')
writer.close()
asset = store.import_file(root / 'source.pdf')
asset['pages'] = 3
# Use a genuine data URL, as saved by the application's photograph picker.
picture = QImage(640, 360, QImage.Format.Format_RGB32)
picture.fill(0xffd7e1eb)
image_data = QBuffer()
image_data.open(QIODevice.OpenModeFlag.WriteOnly)
assert picture.save(image_data, 'PNG')
photo = 'data:image/png;base64,' + base64.b64encode(bytes(image_data.data())).decode()
image_data.close()
output = Path(__file__).resolve().parents[1] / 'tmp/pdfs/assembly-example.pdf'
output.parent.mkdir(parents=True, exist_ok=True)
window = Window(store, test_profile=True)
window.show()
stage = 0
errors = []


def fail(value):
    errors.append(str(value))
    application.exit(1)


def ready(value):
    global stage
    if stage or not value:
        return
    stage = 1
    script = r'''(async()=>{try{
      S=seed();S.projects=S.projects.slice(0,1);const p=S.projects[0];
      p.admin=[];p.materials=[];p.journals=[];p.surveys=[];p.opsDocs=[];p.systems=p.systems.slice(0,1);
      const s=p.systems[0];s.subprofiles=s.subprofiles.slice(0,1);s.aik=[];s.journals=[];s.sketches=[];
      s.scheme.file='';s.scheme.fileKey='';s.acts=s.acts.slice(0,2);s.scheme.frameEnabled=false;
      const a=s.acts[0],other=s.acts[1];
      a.type='АОСР';a.subs=[s.subprofiles[0].id];a.materials=[];a.scan={file:'',pages:0};a.schemes=[];a.tests=[];a.testLinks=[];
      a.photos=[{id:'photo1',img:PHOTO,cap:'Монтаж участка 1'},{id:'photo2',img:PHOTO,cap:'Монтаж участка 2'}];a.photoLayout=2;
      other.type='АОСР';other.subs=[];other.schemes=[{id:'outside',frameEnabled:false,name:'Листы из отдельной схемы',file:'source.pdf',fileKey:ASSET.id,pages:3}];
      other.schemeLinks=[];other.testLinks=[];other.photos=[];other.materials=[];
      a.schemeLinks=[{id:'outside',from:2,to:3}];
      s.trials=[{id:'protocol1',name:'Протокол проверки',num:'П-01',date:'2026-10-02',file:'source.pdf',fileKey:ASSET.id,pages:1}];
      S.volCfg={};IX=null;ensureWorkspace();save();await desktopFlush(true);
      const vol=volumeList(p).find(v=>v.s);history.replaceState(null,'','#/build/'+p.id+'/'+vol.key);render();
      if(!document.querySelector('[data-a="assemblyRun"]'))throw Error('No PDF button');
      const plan=pdfPlan(p,[vol]),link=plan.volumes[0].documents.find(x=>x.id.startsWith('linked:'));
      if(!link||link.from!==2||link.to!==3)throw Error('Selected sheets missing');
      const all=await A.downloadAssemblyPdf({all:'1'});if(!all)throw Error(document.querySelector('#modal-root').innerText);
      // A missing real source must produce a useful error rather than an incomplete download.
      s.trials[0].fileKey='';const blocked=await A.downloadAssemblyPdf({all:'1'});
      if(blocked||!document.querySelector('#modal-root').innerText.includes('Протокол проверки'))throw Error('Missing source not reported');
      window.pdfSmokeResult=JSON.stringify({ok:true,pages:all.pages,link:link.id});
    }catch(e){window.pdfSmokeResult=JSON.stringify({ok:false,error:e.stack});}})();'''
    script = script.replace('ASSET', json.dumps(asset)).replace('PHOTO', json.dumps(photo))
    window.page.runJavaScript(script)


def finished(value):
    global stage
    if stage != 1 or not value:
        return
    try:
        result = json.loads(value)
        assert result['ok'], result
        reader = PdfReader(output)
        assert len(reader.pages) == result['pages']
        text = '\n'.join(page_text(page) for page in reader.pages)
        assert 'Фототаблица' in text
        assert 'Монтаж' in text
        assert 'все' not in window.page.console_errors
        assert not window.page.console_errors, window.page.console_errors
        assert sum('ЛИСТ ИСХОДНОЙ СХЕМЫ 1' in page_text(page) for page in reader.pages) == 1
        assert sum('ЛИСТ ИСХОДНОЙ СХЕМЫ 2' in page_text(page) for page in reader.pages) == 2
        assert sum('ЛИСТ ИСХОДНОЙ СХЕМЫ 3' in page_text(page) for page in reader.pages) == 2
        assert reader.outline
        stage = 2
        window.grab().save(str(output.with_suffix('.png')))
        print('PASS: real PDF buttons, all volumes, generated act, photos, selected sheets, actual registry, missing source reporting')
        timer.stop()
        window.close()
    except Exception as exc:
        fail(exc)


def poll():
    if not stage:
        window.page.runJavaScript('window.desktopReady===true', ready)
    elif stage == 1:
        window.page.runJavaScript('window.pdfSmokeResult||null', finished)


timer = QTimer()
timer.timeout.connect(poll)
timer.start(200)
QTimer.singleShot(60000, lambda: fail('PDF UI test timed out'))
with patch('drawing_frame.resolve_frame_font', return_value='DejaVu Sans'), patch('app.QFileDialog.getSaveFileName', return_value=(str(output), 'PDF')):
    code = application.exec()
dispose_window(window)
store.close()
work.cleanup()
if errors:
    print('\n'.join(errors), file=sys.stderr)
sys.exit(code)
