"""СтройИД Desktop 0.9.5. Windows packaging entry point."""

from __future__ import annotations
from stroyid.resources import UI_ROOT
import os
import sys
import hashlib
from pathlib import Path
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QLockFile,
    QStandardPaths,
    QTimer,
    QUrl,
    QSettings,
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from stroyid.infrastructure.storage import Store


from .bridge import Bridge


class LocalPage(QWebEnginePage):
    def __init__(self, profile, ui_url, parent):
        super().__init__(profile, parent)
        self.ui_url = ui_url
        self.console_errors = []

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        # HTML/CSV exports are local Blob URLs intercepted by downloadRequested.
        return url.toLocalFile() == self.ui_url.toLocalFile() or url.scheme() in ("about", "blob")

    def javaScriptConsoleMessage(self, level, message, line, source):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            self.console_errors.append(message)
        print(f"UI [{level}] {line}: {message}", file=sys.stderr)


class Window(QMainWindow):
    def __init__(self, store, *, test_profile=False):
        super().__init__()
        self.store = store
        self.closing = self.allow_close = False
        self.setWindowTitle("СтройИД")
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
            self.profile = QWebEngineProfile("stroiid-desktop", self)
            self.profile.setPersistentStoragePath(
                str(
                    Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))
                    / "webprofile"
                )
            )
            self.profile.setCachePath(
                str(
                    Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) / "webcache"
                )
            )
        ui_url = QUrl.fromLocalFile(str(UI_ROOT / "index.html"))
        self.page = LocalPage(self.profile, ui_url, self.view)
        self.view.setPage(self.page)
        self.bridge = Bridge(store, self)
        self.setWindowIcon(QIcon(str(UI_ROOT / "stroyid.ico")))
        self.channel = QWebChannel(self.page)
        self.channel.registerObject("desktop", self.bridge)
        self.page.setWebChannel(self.channel)
        self.profile.downloadRequested.connect(self.download)
        menu = self.menuBar().addMenu("Приложение")
        for title, js in [
            ("Сохранить сейчас", "A.desktopSave()"),
            (
                "Сделать снимок сборки",
                "const p=curProject();if(p)A.assemblySnapshot({p:p.id});else toast('Откройте объект');",
            ),
            ("Показать папку данных", "A.showInFolder()"),
        ]:
            action = QAction(title, self)
            action.triggered.connect(
                lambda checked=False, script=js: self.page.runJavaScript(script)
            )
            menu.addAction(action)
        self.view.setUrl(ui_url)

    def download(self, request):
        name = Path(request.suggestedFileName()).name or "document.html"
        target, _ = QFileDialog.getSaveFileName(self, "Сохранить документ", name, "Все файлы (*)")
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
            QMessageBox.warning(
                self,
                "Сохранение не завершено",
                "Окно осталось открытым. Повторите попытку закрытия после сохранения.",
            )


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
    app.setApplicationName("StroyID")
    app.setWindowIcon(QIcon(str(UI_ROOT / "stroyid.ico")))
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StroyID.Desktop.0.9")
    app.setOrganizationName("StroyID")
    settings = QSettings()
    selected = (
        os.environ.get("STROYID_DATA_DIR")
        or settings.value("workspace")
        or QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
    )
    dialog = QMessageBox(None)
    dialog.setWindowTitle("Папка базы СтройИД")
    dialog.setText("Продолжить работу с этой папкой?\n\n" + str(selected))
    dialog.setInformativeText(
        "Можно выбрать общую папку Яндекс Диска, хранящуюся на этом компьютере."
    )
    stay = dialog.addButton("Открыть эту папку", QMessageBox.ButtonRole.AcceptRole)
    other = dialog.addButton("Выбрать другую", QMessageBox.ButtonRole.ActionRole)
    dialog.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
    dialog.exec()
    if dialog.clickedButton() == other:
        selected = QFileDialog.getExistingDirectory(None, "Папка базы СтройИД", str(selected))
        if not selected:
            return 0
    elif dialog.clickedButton() != stay:
        return 0
    while selected:
        root = Path(selected).resolve()
        root.mkdir(parents=True, exist_ok=True)
        settings.setValue("workspace", str(root))
        cache = Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))
        cache.mkdir(parents=True, exist_ok=True)
        # The process lock is local to this PC; it is deliberately outside Yandex Disk.
        lock = QLockFile(str(cache / (hashlib.sha256(str(root).encode()).hexdigest() + ".lock")))
        if not lock.tryLock(0):
            QMessageBox.information(
                None, "СтройИД уже запущен", "На этом компьютере папка уже открыта."
            )
            return 1
        try:
            store = Store(root)
            window = Window(store)
            window.show()
            result = app.exec()
            selected = window.next_root
            dispose_window(window)
            store.close()
        except Exception as exc:
            QMessageBox.critical(None, "Папка не открыта", str(exc))
            return 1
        finally:
            lock.unlock()
    return result


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from stroyid.presentation.desktop.self_test import run

        position = sys.argv.index("--self-test")
        target = sys.argv[position + 1] if len(sys.argv) > position + 1 else "self-test-report.json"
        sys.exit(run(target))
    sys.exit(main())
