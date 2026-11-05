# Build on Windows x64 with Python 3.12/3.13. PyInstaller's PySide6 hooks collect QtWebEngine.
from pathlib import Path
project = Path(SPECPATH)
a = Analysis([str(project / 'app.py')], pathex=[str(project / "src")],
             binaries=[], datas=[(str(project / 'ui'), 'ui'),
                                 (str(project / 'THIRD_PARTY.md'), '.'),
                                 (str(project / 'README.md'), '.')],
             hiddenimports=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
                            'PySide6.QtWebChannel', 'PySide6.QtPdf', 'PySide6.QtPrintSupport'],
             # The UI uses Qt Widgets and local HTML. Qt DLL dependencies are still
             # collected, but importing QtQml would also bundle every QML plugin.
             hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['PySide6.QtQml'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='StroyID',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, icon=str(project/'ui/stroyid.ico'))
