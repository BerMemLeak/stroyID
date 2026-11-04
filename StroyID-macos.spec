# Native Apple Silicon .app, with Qt frameworks and the embedded UI.
from pathlib import Path
project = Path(SPECPATH)
a = Analysis([str(project/'app.py')], pathex=[str(project)],
             binaries=[], datas=[(str(project/'ui'), 'ui'),
                                 (str(project/'THIRD_PARTY.md'), '.'),
                                 (str(project/'README.md'), '.')],
             hiddenimports=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
                            'PySide6.QtWebChannel', 'PySide6.QtPdf', 'PySide6.QtPrintSupport'],
             hookspath=[str(project/'tools/pyinstaller-hooks')], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='StroyID',
          debug=False, strip=False, upx=False, console=False, target_arch='arm64',
          argv_emulation=False, codesign_identity=None,
          entitlements_file=str(project/'tools/macos-entitlements.plist'))
collection = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='StroyID')
app = BUNDLE(collection, name='StroyID.app',
             icon=str(project/'build/macos/StroyID.icns'),
             bundle_identifier='ru.stroyid.desktop', version='0.9.5',
             info_plist={'CFBundleDisplayName': 'СтройИД',
                         'LSMinimumSystemVersion': '13.0',
                         'NSHighResolutionCapable': True,
                         'NSAppleEventsUsageDescription': 'СтройИД использует Microsoft Word для формирования PDF из ваших шаблонов.'})
