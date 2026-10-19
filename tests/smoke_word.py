"""Verify native DOCX import, per-object/profile choices, Word preview and PDF integration.
Word's COM renderer is replaced only in this wiring test; it needs no installed Office.
"""
import html
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader
from app import Window, dispose_window
from storage import Store
from word_templates import sample_docx, package, inspect_docx
from pdf_export import render_html
from pdf_text import page_text

application = QApplication.instance() or QApplication([])
work = tempfile.TemporaryDirectory(prefix='stroiid-word-ui-')
root = Path(work.name)
store = Store(root / 'data')
act = sample_docx('aosr', 'ШАБЛОН ОБЪЕКТА', root / 'Акт.docx')
profile_act = sample_docx('aosr', 'ШАБЛОН ЗАКАЗЧИКА', root / 'Акт заказчика.docx')
title = sample_docx('title', 'ТИТУЛ WORD', root / 'Титул.docx')
reg = sample_docx('reg', 'РЕЕСТР WORD', root / 'Реестр.docx')
signed = root / 'signed.pdf'
render_html('<h2>ПОДПИСАННЫЙ СКАН</h2>', signed)
signed_asset = store.import_file(signed)
original = act.read_bytes()
output = Path(__file__).resolve().parents[1] / 'tmp/word/word-ui-assembly.pdf'
output.parent.mkdir(parents=True, exist_ok=True)
opened = []
conversions = []


def fake_word_open(path):
    opened.append(Path(path).read_bytes())
    return True


def fake_word_converter(jobs):
    for source, target in jobs:
        assert inspect_docx(Path(source).read_bytes())['tags'] == []
        text = '\n'.join(ET.fromstring(package(Path(source).read_bytes())['word/document.xml']).itertext())
        conversions.append(text)
        render_html('<p>' + html.escape(text).replace('\n', '<br>') + '</p>', target)


window = Window(store, test_profile=True)
window.resize(1600, 1000)
window.show()
stage, errors = 0, []


def fail(error):
    errors.append(str(error))
    application.exit(1)


def ready(value):
    global stage
    if stage or not value:
        return
    stage = 1
    script = r'''(async()=>{try{
      S=seed();S.projects.forEach(p=>p.systems.forEach(s=>s.acts.forEach(a=>a.quantityEnabled=false)));S.projects=S.projects.slice(0,1);const p=S.projects[0];
      p.name='Объект для Word';p.admin=[];p.materials=[];p.journals=[];p.surveys=[];p.opsDocs=[];p.systems=p.systems.slice(0,1);
      const s=p.systems[0];s.subprofiles=s.subprofiles.slice(0,1);s.aik=[];s.journals=[];s.sketches=[];s.trials=[];s.scheme.file='';s.scheme.fileKey='';s.acts=s.acts.slice(0,1);
      const a=s.acts[0];a.type='АОСР';a.subs=[s.subprofiles[0].id];a.materials=[];a.scan={file:'',pages:0};a.schemes=[];a.tests=[];a.testLinks=[];a.schemeLinks=[];a.photos=[];
      const p2=clone(p);p2.id='P2';p2.name='Второй объект';p2.systems=[];S.projects.push(p2);
      IX=null;ensureWorkspace();S.volCfg={};S.ui.wordObject=p.id;S.ui.wordProfile='';save();await desktopFlush(true);go('#/lib/templates');render();
      if(document.querySelectorAll('[data-word-section]').length!==13)throw Error('Sections missing');
      await A.tplAdd({section:'aosr'});const basic=S.lib.templates.at(-1);
      if(!basic.fileKey||basic.type!=='АОСР')throw Error('DOCX was not stored');
      await A.wordSelect({id:basic.id,section:'aosr'});
      if(p2.wordTemplates.aosr)throw Error('Selection leaked to another object');
      const vol=volumeList(p).find(v=>v.s);if(wordChoice(p,vol,'aosr').id!==basic.id)throw Error('Base choice not effective');
      await A.wordOpen({id:basic.id});await A.wordPreview({id:basic.id});
      await A.tplAdd({section:'aosr'});const profile=S.lib.templates.at(-1);
      S.ui.wordProfile=s.subprofiles[0].profileId;render();await A.wordSelect({id:profile.id,section:'aosr'});
      if(wordChoice(p,vol,'aosr').id!==profile.id||p.wordTemplates.aosr!==basic.id)throw Error('Profile choice did not override independently');
      S.ui.wordProfile='';await A.tplAdd({section:'title'});await A.wordSelect({id:S.lib.templates.at(-1).id,section:'title'});
      await A.tplAdd({section:'reg'});await A.wordSelect({id:S.lib.templates.at(-1).id,section:'reg'});
      const plan=pdfPlan(p,[vol]);if(plan.volumes[0].documents.find(x=>x.id==='a'+a.id).templateKey!==profile.fileKey)throw Error('PDF did not use customer template');
      a.scan={file:'signed.pdf',fileKey:SIGNED.id,pages:1};
      if(pdfPlan(p,[vol]).volumes[0].documents.find(x=>x.id==='a'+a.id).kind!=='pdf')throw Error('Signed original was replaced by a Word form');
      a.scan.fileKey='';
      if(pdfPlan(p,[vol]).volumes[0].documents.find(x=>x.id==='a'+a.id).kind!=='pdf')throw Error('Missing signed source was silently replaced by an unsigned form');
      a.scan={file:'',pages:0};save();await desktopFlush(true);
      history.replaceState(null,'','#/build/'+p.id+'/'+vol.key);render();const result=await A.downloadAssemblyPdf({all:'1'});if(!result)throw Error(document.querySelector('#modal-root').innerText);
      closeModal();S.ui.wordObject=p.id;S.ui.wordProfile=s.subprofiles[0].profileId;S.ui.wordOpen={aosr:true};go('#/lib/templates');render();save();await desktopFlush(true);
      await A.wordSample({section:'spj'});if(!S.lib.templates.at(-1).fileKey)throw Error('Example DOCX not created');
      const backup=await nativeCall('backup',{reason:'Word test',state:S});
      window.wordSmokeResult=JSON.stringify({ok:true,pages:result.pages,backup:backup.path,basic:basic.id,profile:profile.id});
    }catch(e){window.wordSmokeResult=JSON.stringify({ok:false,error:e.stack});}})();'''.replace('SIGNED', json.dumps(signed_asset))
    window.page.runJavaScript(script)


def finished(value):
    global stage
    if stage != 1 or not value:
        return
    try:
        result = json.loads(value)
        assert result['ok'], result
        assert not window.page.console_errors, window.page.console_errors
        assert len(opened) == 2
        assert inspect_docx(opened[0])['tags']
        assert inspect_docx(opened[1])['tags'] == []
        assert 'Объект для Word' in ''.join(ET.fromstring(package(opened[1])['word/document.xml']).itertext())
        assert act.read_bytes() == original
        reader = PdfReader(output)
        assert len(reader.pages) == result['pages']
        text = '\n'.join(page_text(p) for p in reader.pages)
        assert 'ШАБЛОН ЗАКАЗЧИКА' in text and 'ТИТУЛ WORD' in text and 'РЕЕСТР WORD' in text
        assert 'ШАБЛОН ОБЪЕКТА' not in text
        assert conversions
        restored = Store(root / 'restored')
        try:
            archive = root / 'transfer.zip'
            store.export_backup(Path(result['backup']).name, archive)
            loaded = restored.restore(archive)['state']
            assert loaded['projects'][0]['wordTemplates']['aosr'] == result['basic']
            assert loaded['projects'][1]['wordTemplates'] == {}
            for t in loaded['lib']['templates']:
                if t.get('fileKey'):
                    inspect_docx(restored.asset_path(t['fileKey'])[0].read_bytes())
        finally:
            restored.close()
        # Capture the catalogue with actual imported Word files.
        window.page.runJavaScript("document.querySelector('#toast').innerHTML='';document.querySelector('[data-word-section=\"aosr\"]').scrollIntoView({block:'center'})")
        QTimer.singleShot(200, capture_and_close)
        stage = 2
        print('PASS: DOCX import, Word opening, filled preview, document sections and HTML frame, object/profile isolation, signed-PDF priority, full PDF with Word forms and registry, DOCX backup/restore')
    except Exception as exc:
        fail(exc)


def capture_and_close():
    window.grab().save(str(output.with_suffix('.png')))
    timer.stop()
    window.close()


def poll():
    if not stage:
        window.page.runJavaScript('window.desktopReady===true', ready)
    elif stage == 1:
        window.page.runJavaScript('window.wordSmokeResult||null', finished)


timer = QTimer()
timer.timeout.connect(poll)
timer.start(150)
QTimer.singleShot(60000, lambda: fail('Word UI test timed out'))
with patch('app.QFileDialog.getOpenFileName', side_effect=[(str(x), 'DOCX') for x in (act, profile_act, title, reg)]), \
     patch('app.QFileDialog.getSaveFileName', return_value=(str(output), 'PDF')), \
     patch('word_templates.open_in_word', side_effect=fake_word_open), \
     patch('pdf_export.convert_docx_batch', side_effect=fake_word_converter):
    code = application.exec()
dispose_window(window)
store.close()
work.cleanup()
if errors:
    print('\n'.join(errors), file=sys.stderr)
sys.exit(code)
