"""Native macOS bundle validation and distributable ZIP/DMG creation."""
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def require_native_mac():
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise RuntimeError('Сборку macOS нужно запускать на Apple Silicon с ARM64 Python, без Rosetta.')


def make_icon():
    require_native_mac()
    from PySide6.QtCore import QRectF, QSize
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    app = QGuiApplication.instance() or QGuiApplication([])
    root = ROOT/'build/macos'
    iconset = root/'StroyID.iconset'
    iconset.mkdir(parents=True, exist_ok=True)
    svg = QSvgRenderer(str(ROOT/'ui/stroyid.svg'))
    if not svg.isValid():
        raise ValueError('Не удалось прочитать значок приложения')
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = size * scale
            image = QImage(QSize(pixels, pixels), QImage.Format.Format_ARGB32)
            image.fill(0)
            painter = QPainter(image)
            svg.render(painter, QRectF(0, 0, pixels, pixels))
            painter.end()
            if not image.save(str(iconset/f'icon_{size}x{size}{"@2x" if scale==2 else ""}.png')):
                raise ValueError('Не удалось сохранить значок приложения')
    subprocess.run(['/usr/bin/iconutil', '-c', 'icns', str(iconset), '-o', str(root/'StroyID.icns')], check=True, timeout=60)


def validate_bundle(bundle):
    require_native_mac()
    bundle = Path(bundle)
    with (bundle/'Contents/Info.plist').open('rb') as file:
        info = plistlib.load(file)
    if info.get('CFBundleIdentifier') != 'ru.stroyid.desktop' or not info.get('NSAppleEventsUsageDescription'):
        raise ValueError('В приложении отсутствуют настройки автоматизации Word')
    binary = bundle/'Contents/MacOS'/info['CFBundleExecutable']
    architecture = subprocess.check_output(['/usr/bin/lipo', '-archs', str(binary)], text=True).strip()
    if architecture != 'arm64':
        raise ValueError('Приложение собрано не для Apple Silicon: ' + architecture)
    helpers = list(bundle.rglob('QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess'))
    if not helpers:
        raise ValueError('В сборке отсутствует QtWebEngineProcess')
    for helper in helpers:
        subprocess.run(['/usr/bin/lipo', str(helper), '-verify_arch', 'arm64'], check=True, timeout=20)
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(bundle)], check=True, timeout=120)
    return {'architecture': architecture, 'bundle_id': info['CFBundleIdentifier'],
            'signature': 'ad-hoc', 'notarized': False, 'webengine_helpers': len(helpers)}


def package(bundle, output):
    require_native_mac()
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stroiid-package-', dir=output) as temporary:
        temporary = Path(temporary)
        archive = temporary/'StroyID-macOS-arm64.zip'
        subprocess.run(['/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(bundle), str(archive)], check=True, timeout=300)
        stage = temporary/'image'
        stage.mkdir()
        shutil.copytree(bundle, stage/'StroyID.app', symlinks=True)
        (stage/'Applications').symlink_to('/Applications', target_is_directory=True)
        image = temporary/'StroyID-macOS-arm64.dmg'
        subprocess.run(['/usr/bin/hdiutil', 'create', '-volname', 'СтройИД', '-srcfolder', str(stage),
                        '-format', 'UDZO', '-ov', str(image)], check=True, timeout=300)
        # Validate the archive the user will receive, not just the build directory.
        extracted = temporary/'relocated'
        subprocess.run(['/usr/bin/ditto', '-x', '-k', str(archive), str(extracted)], check=True, timeout=180)
        validate_bundle(extracted/'StroyID.app')
        subprocess.run(['/usr/bin/hdiutil', 'verify', str(image)], check=True, timeout=120)
        files=[]
        for file in (archive, image):
            target = output/file.name
            os.replace(file, target)
            files.append(target)
        return files


if __name__ == '__main__':
    if sys.argv[1:] == ['icon']:
        make_icon()
    else:
        raise SystemExit('Usage: macos_release.py icon')
