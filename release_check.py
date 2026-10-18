"""Integration test executed by the packaged application itself, in an isolated database."""
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def run(report_path):
    for stream in (sys.stdout,sys.stderr):
        if stream is not None and hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='backslashreplace')
    from PySide6.QtCore import QTimer, qVersion
    from PySide6.QtGui import QPainter, QPdfWriter
    from PySide6.QtWidgets import QApplication
    from app import Window, dispose_window
    from storage import Store

    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'version': '0.9.4', 'passed': False, 'platform': platform.platform(), 'python': sys.version,
              'qt': qVersion(), 'frozen': bool(getattr(sys, 'frozen', False)), 'checks': [], 'errors': []}
    app = QApplication.instance() or QApplication([])
    stage = 0
    with tempfile.TemporaryDirectory(prefix='stroiid-release-check-') as work:
        work = Path(work)
        store = Store(work / 'isolated-data')
        window = Window(store, test_profile=True)
        assert window.profile.isOffTheRecord()
        window.show()
        pdf = work / 'Исходник с двумя страницами.pdf'
        writer = QPdfWriter(str(pdf))
        painter = QPainter(writer)
        painter.drawText(30, 100, 'Page one')
        writer.newPage()
        painter.drawText(30, 100, 'Page two')
        painter.end()
        del painter, writer
        export = work / 'export.csv'
        pdf_export = work / 'Вся исполнительная документация.pdf'

        def fail(message):
            report['errors'].append(str(message))
            print('SELF-TEST FAILED: ' + str(message), file=sys.stderr, flush=True)
            app.exit(1)

        def started(ready):
            nonlocal stage
            if stage or not ready:
                return
            stage = 1
            print('SELF-TEST: local interface ready', flush=True)
            try:
                from word_templates import fill_docx, inspect_docx
                sample = json.loads(window.bridge.request('sampleDocx', json.dumps(
                    {'section': 'title', 'title': 'Титульный лист'})))
                assert sample['ok'], sample
                docx, _ = store.asset_path(sample['value']['id'])
                values = {tag: 'Проверочный объект' for tag in sample['value']['tags']}
                filled = fill_docx(docx.read_bytes(), work / 'Заполненный Word.docx', values)
                assert inspect_docx(filled.read_bytes())['tags'] == []
                report['checks'].append('packed_docx_engine_and_native_sample')
                result = json.loads(window.bridge.request('pickPdf', '{}'))
                if not result['ok']:
                    raise ValueError(result['error'])
                asset = result['value']
                assert asset['pages'] == 2
                assert store.asset_path(asset['id'])[0].read_bytes() == pdf.read_bytes()
                report['checks'].append('qt_pdf_import_and_original_file')
                script = '''(async()=>{try{
                  if(S.projects.length!==0)throw Error('Self-test must use an empty isolated database');
                  A.newProject();document.querySelector('#np-n').value='Проверочный объект';MB[1].f();
                  const p=S.projects[0];A.newSystem({p:p.id});
                  document.querySelector('input[name=ns][value="ВК"]').checked=true;MB[1].f();
                  const s=p.systems[0];A.newAct({s:s.id});MB[1].f();
                  const a=s.acts[0];a.scan={file:ASSET.name,fileKey:ASSET.id,pages:ASSET.pages};
                  Object.assign(s.scheme,{file:ASSET.name,fileKey:ASSET.id,pages:ASSET.pages,frameEnabled:true});
                  S.meta.name='До восстановления';save();await desktopFlush(true);await desktopFlush(true);
                  const b=await backup('Проверка упакованного приложения');
                  S.meta.name='После изменения';save();await desktopFlush(true);
                  const restored=await nativeCall('restore',{id:b.id});
                  acceptFolder(restored);desktopDirty=false;desktopPending=null;IX=null;ensureWorkspace();
                  if(S.meta.name!=='До восстановления')throw Error('ZIP restoration failed');
                  for(const route of ['#/home','#/p/'+p.id,'#/s/'+s.id,'#/a/'+a.id,'#/lib/templates','#/settings/general','#/settings/backups']){
                    history.replaceState(null,'',route);render();
                    if(document.querySelector('#content').innerText.includes('Ошибка отображения'))throw Error(route);
                  }
                  download('export.csv','СтройИД;123\\n','text/csv;charset=utf-8');
                  history.replaceState(null,'','#/build/'+p.id);render();
                  if(!document.querySelector('[data-a="assemblyRun"]'))throw Error('PDF download button missing');
                  const saved=await A.downloadAssemblyPdf({all:'1'});
                  if(!saved||saved.pages<4)throw Error('PDF assembly failed');
                  window.releaseResult={ok:true};
                }catch(e){window.releaseResult={ok:false,error:e.stack};}})();'''
                script = script.replace('ASSET', json.dumps(asset, ensure_ascii=False))
                window.page.runJavaScript(script)
                print('SELF-TEST: checking workflow and file export', flush=True)
            except Exception as exc:
                fail(exc)

        def finished(value):
            nonlocal stage
            if stage != 1 or not value:
                return
            try:
                value = json.loads(value)
                if not value['ok']:
                    raise ValueError(value['error'])
                if not export.exists():
                    return  # asynchronous Chromium download still in progress
                assert 'СтройИД;123' in export.read_text(encoding='utf-8-sig')
                from pypdf import PdfReader
                assembled = PdfReader(pdf_export)
                assert len(assembled.pages) >= 4
                assert assembled.outline
                assert not window.page.console_errors, window.page.console_errors
                loaded = store.load()['state']
                assert len(loaded['projects'][0]['systems'][0]['acts']) == 1
                assert len(store.list_backups()) >= 2
                report['checks'].extend(['local_html_and_webchannel', 'new_object_system_act',
                                         'folder_save_queue', 'zip_backup_and_restore', 'native_csv_download',
                                         'native_complete_object_pdf_export'])
                stage = 2
                timer.stop()
                window.page.runJavaScript("S.meta.name='Сохранено при закрытии';save()", lambda _: window.close())
            except Exception as exc:
                fail(exc)

        def poll():
            if not stage:
                window.page.runJavaScript('window.desktopReady===true', started)
            elif stage == 1:
                window.page.runJavaScript('window.releaseResult?JSON.stringify(window.releaseResult):null', finished)

        timer = QTimer()
        timer.timeout.connect(poll)
        timer.start(200)
        QTimer.singleShot(60000, lambda: fail('Packaged application self-test timed out'))
        with patch('app.QFileDialog.getOpenFileName', return_value=(str(pdf), 'PDF')), \
             patch('app.QFileDialog.getSaveFileName', side_effect=lambda *args:
                   (str(pdf_export), 'PDF') if args[-1] == 'PDF (*.pdf)' else (str(export), 'CSV')):
            code = app.exec()
        timer.stop()
        dispose_window(window)
        store.close()
        if code == 0 and stage == 2 and not report['errors']:
            reopened = Store(work / 'isolated-data')
            try:
                assert reopened.load()['state']['meta']['name'] == 'Сохранено при закрытии'
                assert len(reopened.list_backups()) >= 2
                report['checks'].append('close_flush_and_reopen_database')
                report['passed'] = True
            except Exception as exc:
                report['errors'].append(str(exc))
            finally:
                reopened.close()
        assert not (work / 'isolated-data/webprofile').exists()
        assert not (work / 'isolated-data/webcache').exists()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['passed'] else 1
