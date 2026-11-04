"""Collect Qt's helper under the framework's binary version, not Resources.

Some PySide wheels contain Versions/Resources alongside Versions/A. PyInstaller
6.22.3 sorts both names and treats Resources as a version, producing a framework
that fails Apple's strict signature validation. Keep its dependency collection,
but correct that destination before binary processing and framework symlinking.
"""
from pathlib import Path
from PyInstaller import compat
from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
web_binaries, web_datas = pyside6_library_info.collect_qtwebengine_files()

if compat.is_darwin:
    framework = Path(pyside6_library_info.location['LibrariesPath'])/'QtWebEngineCore.framework'
    if framework.is_dir():
        versions = [p.name for p in (framework/'Versions').iterdir()
                    if p.name != 'Current' and (p/'QtWebEngineCore').is_file()]
        if len(versions) != 1:
            raise RuntimeError('Expected one binary version of QtWebEngineCore.framework: '+repr(versions))
        version = versions[0]
        def correct_destinations(entries):
            return [(source, destination.replace('QtWebEngineCore.framework/Versions/Resources/',
                                                 'QtWebEngineCore.framework/Versions/'+version+'/'))
                    for source, destination in entries]
        web_binaries = correct_destinations(web_binaries)
        web_datas = correct_destinations(web_datas)
        print('QtWebEngineCore helper/resource framework version: '+version, flush=True)

binaries += web_binaries
datas += web_datas
hiddenimports += ['PySide6.QtPrintSupport']
