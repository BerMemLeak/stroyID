"""СтройИД Desktop 0.9.5. Windows packaging entry point."""
from __future__ import annotations
import json
import os
import shutil
import sys
import tempfile
import hashlib
from pathlib import Path
from PySide6.QtCore import QObject, QCoreApplication, QEvent, QLockFile, QStandardPaths, QTimer, QUrl, QFileSystemWatcher, Signal, Slot, QSettings
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtPdf import QPdfDocument
from storage import Store, validate_state


class Bridge(QObject):
    flushRequested = Signal()
    asyncReply = Signal(str,str)
    folderChanged = Signal()

    def __init__(self, store, window):
        super().__init__(window)
        self.store, self.window = store, window
        from concurrent.futures import ThreadPoolExecutor
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='StroyID-storage')
        self.watcher=QFileSystemWatcher(self)
        self.watchTimer=QTimer(self);self.watchTimer.setSingleShot(True);self.watchTimer.setInterval(400)
        self.watcher.fileChanged.connect(lambda _:self.watchTimer.start())
        self.watcher.directoryChanged.connect(lambda _:self.watchTimer.start())
        self.watchTimer.timeout.connect(self.notify_external_change)
        self.watchStamp=None
        self.observedPaths=set()
        # Some native directory notifications omit in-place writes. On Windows
        # check only metadata periodically; never reload or hash an unchanged DB.
        self.metadataTimer=QTimer(self);self.metadataTimer.setInterval(3000)
        self.metadataTimer.timeout.connect(self.notify_external_change)
        if os.name=='nt':self.metadataTimer.start()
        self.asyncReply.connect(self.refresh_watches)

    @Slot(str,str,str)
    def requestAsync(self, token, operation, payload):
        def complete(future):
            try:self.asyncReply.emit(token,future.result())
            except RuntimeError:pass
        self.executor.submit(self.request,operation,payload).add_done_callback(complete)

    @Slot(str,str)
    def refresh_watches(self, token='', raw=''):
        if raw:
            response=json.loads(raw);value=response.get('value')
            if not isinstance(value,dict) or 'revision' not in value or value.get('preview'):return
        paths={str(self.store.root),str(self.store.events_dir)}
        # Observe file metadata, but register directory handles only.
        # A watcher must not hold the files which atomic saves replace.
        for key,record in list(self.store.latest.items()):
            if not record or record['kind'] in ('history','builds','volume'):continue
            card=self.store.path(self.store.paths[key]);paths.add(str(card))
            from folder_core import walk
            for node in walk(record['data']):
                for field in ('fileKey','photoKey','logoKey','signKey'):
                    if node.get(field):paths.add(str(self.store.path(node[field])))
        for rel in ('Справочники/Материалы и паспорта','Справочники/Профили и шаблоны/Шаблоны Word'):
            folder=self.store.root/rel
            if folder.exists():paths.add(str(folder))
        for name in list(paths):
            parent=Path(name).parent
            while parent.is_relative_to(self.store.root) and parent!=self.store.root:
                if parent.is_relative_to(self.store.service):break
                paths.add(str(parent));parent=parent.parent
        paths={p for p in paths if Path(p).exists()}
        directories={p if Path(p).is_dir() else str(Path(p).parent) for p in paths}
        self.observedPaths=paths|directories
        current=set(self.watcher.files()+self.watcher.directories())
        if current-directories:self.watcher.removePaths(list(current-directories))
        if directories-current:self.watcher.addPaths(list(directories-current))
        self.watchStamp=self.watch_fingerprint()

    def watch_fingerprint(self):
        result=[]
        for path in self.observedPaths:
            try:
                st=Path(path).stat();result.append((path,st.st_mtime_ns,st.st_ctime_ns,st.st_size))
            except OSError:result.append((path,None))
        return tuple(sorted(result))

    @Slot()
    def notify_external_change(self):
        current=self.watch_fingerprint()
        if current!=self.watchStamp:
            self.watchStamp=current;self.folderChanged.emit()

    @Slot(str, str, result=str)
    def request(self, operation, payload):
        try:
            params = json.loads(payload)
            if operation == 'load':
                value = self.store.load()
            elif operation == 'validate':
                value = validate_state(params['state'])
            elif operation == 'save':
                value = self.store.save(params['state'],params['revision'],params.get('baseState'),params.get('baseHeads'))
            elif operation == 'pickPdf':
                name, _ = QFileDialog.getOpenFileName(self.window, 'Выберите исходный PDF', '', 'PDF (*.pdf)')
                if not name:
                    value = None
                else:
                    doc = QPdfDocument(self)
                    error = doc.load(name)
                    if error != QPdfDocument.Error.None_:
                        doc.deleteLater()
                        raise ValueError('PDF не открыт. Проверьте файл; защищённые PDF пока не поддерживаются.')
                    pages = doc.pageCount()
                    doc.close()
                    doc.deleteLater()
                    value = self.store.import_file(name)
                    value['pages'] = pages
            elif operation == 'poll':
                value = self.store.load()
            elif operation == 'repairCard':
                value = self.store.repair(params['key'],params['data'])
            elif operation == 'resolveConflict':
                value = self.store.resolve(params['key'],params['version'])
            elif operation == 'cardData':
                value = self.store.latest.get(params['key'])
            elif operation == 'pickAny':
                name, _ = QFileDialog.getOpenFileName(self.window,'Добавить документ','','Документы (*.pdf *.docx *.doc *.xlsx *.xls *.png *.jpg *.jpeg *.dwg);;Все файлы (*)')
                value = self.store.import_file(name) if name else None
                if value: value['pages'] = self.store._pages(Path(name))
            elif operation == 'pickImage':
                name, _ = QFileDialog.getOpenFileName(self.window,'Фото объекта','','Изображения (*.png *.jpg *.jpeg)')
                value = self.store._image(Path(name)) if name else None
            elif operation == 'switchFolder':
                name = QFileDialog.getExistingDirectory(self.window,'Папка базы СтройИД')
                if name:
                    QSettings().setValue('workspace',name)
                    self.window.next_root = name
                    self.window.close()
                value = bool(name)
            elif operation == 'pickDocx':
                from word_templates import inspect_docx
                name, _ = QFileDialog.getOpenFileName(self.window, 'Загрузить шаблон Word', '', 'Word (*.docx)')
                if not name:
                    value = None
                else:
                    if Path(name).suffix.lower() != '.docx':
                        raise ValueError('Выберите шаблон .docx')
                    details = inspect_docx(Path(name).read_bytes())
                    value = dict(self.store.import_file(name), **details)
            elif operation == 'sampleDocx':
                import re
                from word_templates import sample_docx, inspect_docx
                if not re.fullmatch(r'[a-z]+', str(params['section'])):
                    raise ValueError('Неверный раздел шаблона')
                with tempfile.TemporaryDirectory(prefix='stroiid-sample-') as folder:
                    target = Path(folder) / ('Образец_' + str(params['section']) + '.docx')
                    sample_docx(params['section'], params['title'], target)
                    value = dict(self.store.import_file(target), **inspect_docx(target.read_bytes()))
            elif operation == 'saveGeneratedDocx':
                from pdf_export import word_template_path
                from word_templates import fill_docx
                source = word_template_path(self.store, params)
                name, _ = QFileDialog.getSaveFileName(self.window, 'Сохранить ведомость',
                    Path(params.get('filename', 'Ведомость.docx')).name, 'Word (*.docx)')
                value = None
                if name:
                    target = Path(name).with_suffix('.docx').resolve()
                    if target == self.store.root or self.store.root in target.parents:
                        raise ValueError('Сохраните ведомость вне папки служебных данных')
                    with tempfile.TemporaryDirectory(prefix='stroiid-quantity-') as folder:
                        filled = Path(folder) / 'quantity.docx'
                        fill_docx(source.read_bytes(), filled, params.get('values', {}), params.get('collections', {}))
                        from folder_store import atomic
                        atomic(target, filled.read_bytes())
                    value = str(target)
            elif operation in ('openWordTemplate', 'openFilledWord'):
                import uuid
                from word_templates import fill_docx, open_in_word
                source, name = self.store.asset_path(params['key'])
                cache = Path(tempfile.gettempdir()) / 'StroyID-preview' / uuid.uuid4().hex
                cache.mkdir(parents=True, exist_ok=True)
                target = cache / (Path(name).stem + '.docx')
                if operation == 'openFilledWord':
                    fill_docx(source.read_bytes(), target, params.get('values', {}), params.get('collections', {}))
                else:
                    target = source
                value = open_in_word(target)
            elif operation == 'openAsset':
                path, name = self.store.asset_path(params['key'])
                if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                    raise ValueError('Система не смогла открыть файл. Назначьте приложение для этого формата.')
                value = True
            elif operation == 'openFolder':
                value = QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.root)))
            elif operation == 'backup':
                value = self.store.backup(params.get('reason', 'Вручную'), params.get('state'))
            elif operation == 'listBackups':
                value = self.store.list_backups()
            elif operation == 'restore':
                key = params['id']
                if Path(key).name != key or not key.endswith('.json'):
                    raise ValueError('Неверное имя копии')
                value = self.store.restore(self.store.backups / key)
            elif operation == 'restoreExternal':
                name, _ = QFileDialog.getOpenFileName(self.window, 'Открыть резервную копию', '', 'Копия СтройИД (*.zip)')
                value = self.store.restore(name) if name else None
            elif operation == 'exportBackup':
                key = params['id']
                if Path(key).name != key:
                    raise ValueError('Неверное имя копии')
                source = self.store.backups / key
                target, _ = QFileDialog.getSaveFileName(self.window, 'Сохранить копию вместе с файлами', Path(key).stem+'.zip', 'ZIP (*.zip)')
                if target and Path(target).resolve() != source.resolve():
                    self.store.export_backup(key, target)
                value = bool(target)
            elif operation == 'previewDrawing':
                from drawing_frame import preview
                value = preview(self.store, params)
            elif operation == 'saveFrameTemplate':
                from drawing_frame import TEMPLATE
                target, _ = QFileDialog.getSaveFileName(self.window, 'Сохранить HTML-шаблон рамки', 'Рамка_ГОСТ.html', 'HTML (*.html)')
                if target:
                    Path(target).write_bytes(TEMPLATE.read_bytes())
                value = bool(target)
            elif operation == 'frameFontStatus':
                from drawing_frame import resolve_frame_font
                try:
                    family = resolve_frame_font({'fontKey': params.get('key'), 'requireFont': True}, self.store)
                    value = {'available': True, 'family': family}
                except ValueError:
                    value = {'available': False}
            elif operation == 'pickFrameFont':
                from PySide6.QtGui import QFontDatabase
                name, _ = QFileDialog.getOpenFileName(self.window, 'Шрифт ISOCPEUR', '', 'Шрифты (*.ttf *.otf)')
                value = None
                if name:
                    fid = QFontDatabase.addApplicationFont(name)
                    families = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
                    if not any(f.casefold() == 'isocpeur' for f in families):
                        if fid >= 0: QFontDatabase.removeApplicationFont(fid)
                        raise ValueError('Выбранный файл не содержит шрифт ISOCPEUR')
                    value = self.store.import_file(name)
            elif operation == 'referenceTemplate':
                from word_templates import inspect_docx
                section = params.get('section')
                if section not in ('title', 'reg', 'quantity'):
                    raise ValueError('Неизвестный встроенный шаблон')
                path = Path(__file__).parent / 'ui' / 'reference-templates' / {'title': 'title.docx', 'reg': 'registry.docx', 'quantity': 'quantities.docx'}[section]
                value = {**self.store.import_file(path), **inspect_docx(path.read_bytes())}
            elif operation == 'pickFrameTemplate':
                from drawing_frame import template_svg
                name, _ = QFileDialog.getOpenFileName(self.window, 'HTML-шаблон рамки', '', 'HTML (*.html)')
                value = None
                if name:
                    text = Path(name).read_text('utf-8-sig')
                    import re
                    template_svg(text, {k: '1' for k in re.findall(r'\{\{([^{}]+)\}\}', text)})
                    value = self.store.import_file(name)
            elif operation in ('trashMove','trashRestore','trashPurge','recoverMissing'):
                value = {'trashMove':self.store.move_trash,'trashRestore':self.store.restore_trash,'trashPurge':self.store.purge_trash,'recoverMissing':lambda p:self.store.recover_missing(p['key'])}[operation](params)
            elif operation in ('exportPortable','exportPdfZip','exportRegistry'):
                if self.store.conflicts or self.store.invalid or self.store.missing:
                    raise ValueError('Перед экспортом устраните конфликты и восстановите отсутствующие или повреждённые карточки.')
                filename=Path(params.get('filename') or 'Комплект.zip').name
                if operation=='exportPortable':
                    target,_=QFileDialog.getSaveFileName(self.window,'Сохранить переносимый комплект',filename,'ZIP (*.zip)')
                    if target and not target.lower().endswith('.zip'):target+='.zip'
                    value=self.store.portable_export(params['state'],target) if target else None
                elif operation=='exportPdfZip':
                    from export_jobs import prepare_many,write_many
                    prepared=prepare_many(self.store,params['plans'])
                    target,_=QFileDialog.getSaveFileName(self.window,'Сохранить отдельные PDF в ZIP',filename,'ZIP (*.zip)')
                    if target and not target.lower().endswith('.zip'):target+='.zip'
                    value=write_many(self.store,params['plans'],prepared,target) if target else None
                else:
                    from pdf_export import prepare_export
                    from export_jobs import write_registry
                    prepared=prepare_export(self.store,params['plan']);fmt=params.get('format','xlsx')
                    target,_=QFileDialog.getSaveFileName(self.window,'Сохранить реестр по фактическим страницам',filename,'Excel (*.xlsx)' if fmt=='xlsx' else 'CSV (*.csv)')
                    value=None
                    if target:
                        if Path(target).resolve().is_relative_to(self.store.root):raise ValueError('Сохраните реестр вне рабочей папки базы')
                        if not target.lower().endswith('.'+fmt):target+='.'+fmt
                        write_registry(prepared,target,fmt);value={'path':target,'pages':prepared['pages'],'documents':prepared['documents']}
            elif operation == 'exportPdf':
                from pdf_export import prepare_export, write_export
                if self.store.conflicts or self.store.invalid or self.store.missing or any('Ожида' in w['message'] for w in self.store.warnings):
                    raise ValueError('Перед сборкой исправьте карточки или восстановите файлы:\n'+'\n'.join(dict.fromkeys([str(self.store.paths.get(k,k)) for k in [*self.store.invalid,*self.store.missing,*[c['key'] for c in self.store.conflicts]]]+[w['path']+' — '+w['message'] for w in self.store.warnings])))
                prepared = prepare_export(self.store, params['plan'])
                filename = Path(params.get('filename') or 'Комплект_ИД.pdf').name
                target, _ = QFileDialog.getSaveFileName(self.window,
                    'Сохранить комплект ИД одним PDF', filename, 'PDF (*.pdf)')
                if target:
                    if not target.lower().endswith('.pdf'):
                        target += '.pdf'
                    value = write_export(prepared, target, self.store)
                else:
                    value = None
            else:
                raise ValueError('Неизвестная команда')
            if isinstance(value,dict) and 'revision' in value:value['editHeads']=self.store.base_heads
            return json.dumps({'ok': True, 'value': value}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({'ok': False, 'error': str(exc), 'details':getattr(exc,'details',[])}, ensure_ascii=False)

    @Slot(bool)
    def flushDone(self, success):
        if self.window.closing:
            self.window.closing = False
            if success:
                self.window.allow_close = True
                self.window.close()
            # On failure the WebChannel caller has already shown the detailed
            # error and kept the input. Do not cover it with a second native dialog.


class LocalPage(QWebEnginePage):
    def __init__(self, profile, ui_url, parent):
        super().__init__(profile, parent)
        self.ui_url = ui_url
        self.console_errors = []

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        # HTML/CSV exports are local Blob URLs intercepted by downloadRequested.
        return url.toLocalFile() == self.ui_url.toLocalFile() or url.scheme() in ('about', 'blob')

    def javaScriptConsoleMessage(self, level, message, line, source):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            self.console_errors.append(message)
        print(f'UI [{level}] {line}: {message}', file=sys.stderr)


class Window(QMainWindow):
    def __init__(self, store, *, test_profile=False):
        super().__init__()
        self.store = store
        self.closing = self.allow_close = False
        self.setWindowTitle('СтройИД')
        self.resize(1440, 930)
        self.setMinimumSize(950, 650)
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        self.next_root = None
        if test_profile:
            # Chromium may keep disk-cache files open after Qt window teardown on Windows.
            # Tests keep browser state in memory; actual project data still uses SQLite/files.
            self.profile = QWebEngineProfile(self)
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        else:
            self.profile = QWebEngineProfile('stroiid-desktop', self)
            self.profile.setPersistentStoragePath(str(Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) / 'webprofile'))
            self.profile.setCachePath(str(Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) / 'webcache'))
        ui_url = QUrl.fromLocalFile(str(Path(__file__).resolve().parent / 'ui' / 'index.html'))
        self.page = LocalPage(self.profile, ui_url, self.view)
        self.view.setPage(self.page)
        self.bridge = Bridge(store, self)
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent/'ui/stroyid.ico')))
        self.channel = QWebChannel(self.page)
        self.channel.registerObject('desktop', self.bridge)
        self.page.setWebChannel(self.channel)
        self.profile.downloadRequested.connect(self.download)
        menu = self.menuBar().addMenu('Приложение')
        for title, js in [('Сохранить сейчас', 'A.desktopSave()'),
                          ('Создать резервную копию', 'A.backupNow()'),
                          ('Восстановить из ZIP…', 'A.desktopRestoreExternal()'),
                          ('Показать папку данных', 'A.showInFolder()')]:
            action = QAction(title, self)
            action.triggered.connect(lambda checked=False, script=js: self.page.runJavaScript(script))
            menu.addAction(action)
        self.view.setUrl(ui_url)

    def download(self, request):
        name = Path(request.suggestedFileName()).name or 'document.html'
        target, _ = QFileDialog.getSaveFileName(self, 'Сохранить документ', name, 'Все файлы (*)')
        if target:
            path = Path(target)
            request.setDownloadDirectory(str(path.parent))
            request.setDownloadFileName(path.name)
            request.accept()
        else:
            request.cancel()

    def closeEvent(self, event):
        if self.allow_close:
            event.accept()
            return
        event.ignore()
        if not self.closing:
            self.closing = True
            self.bridge.flushRequested.emit()
            QTimer.singleShot(45000, self.close_timeout)

    def close_timeout(self):
        if self.closing:
            self.closing = False
            QMessageBox.warning(self, 'Сохранение не завершено', 'Окно осталось открытым. Повторите попытку закрытия после сохранения.')


def dispose_window(window):
    window.bridge.watchTimer.stop()
    window.bridge.metadataTimer.stop()
    window.bridge.executor.shutdown(wait=True)
    # Release WebEngine's SQLite handles before temporary test directories are removed on Windows.
    window.view.setPage(QWebEnginePage(window.view))
    window.page.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('StroyID')
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent/'ui/stroyid.ico')))
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('StroyID.Desktop.0.9')
    app.setOrganizationName('StroyID')
    settings=QSettings()
    selected=os.environ.get('STROYID_DATA_DIR') or settings.value('workspace') or QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
    dialog=QMessageBox(None)
    dialog.setWindowTitle('Папка базы СтройИД')
    dialog.setText('Продолжить работу с этой папкой?\n\n'+str(selected))
    dialog.setInformativeText('Можно выбрать общую папку Яндекс Диска, хранящуюся на этом компьютере.')
    stay=dialog.addButton('Открыть эту папку',QMessageBox.ButtonRole.AcceptRole)
    other=dialog.addButton('Выбрать другую',QMessageBox.ButtonRole.ActionRole)
    dialog.addButton('Отмена',QMessageBox.ButtonRole.RejectRole)
    dialog.exec()
    if dialog.clickedButton()==other:
        selected=QFileDialog.getExistingDirectory(None,'Папка базы СтройИД',str(selected))
        if not selected:return 0
    elif dialog.clickedButton()!=stay:return 0
    while selected:
        root=Path(selected).resolve();root.mkdir(parents=True,exist_ok=True)
        settings.setValue('workspace',str(root))
        cache=Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation));cache.mkdir(parents=True,exist_ok=True)
        # The process lock is local to this PC; it is deliberately outside Yandex Disk.
        lock=QLockFile(str(cache/(hashlib.sha256(str(root).encode()).hexdigest()+'.lock')))
        if not lock.tryLock(0):
            QMessageBox.information(None,'СтройИД уже запущен','На этом компьютере папка уже открыта.')
            return 1
        try:
            store=Store(root);window=Window(store);window.show();result=app.exec()
            selected=window.next_root;dispose_window(window);store.close()
        except Exception as exc:
            QMessageBox.critical(None,'Папка не открыта',str(exc));return 1
        finally:lock.unlock()
    return result


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        from release_check import run
        position = sys.argv.index('--self-test')
        target = sys.argv[position + 1] if len(sys.argv) > position + 1 else 'self-test-report.json'
        sys.exit(run(target))
    sys.exit(main())
