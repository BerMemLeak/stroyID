"""Native macOS icon generation and local app validation."""
from pathlib import Path
import platform
import plistlib
import subprocess
import sys

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



if __name__ == '__main__':
    if sys.argv[1:] == ['icon']:
        make_icon()
    else:
        raise SystemExit('Usage: macos_release.py icon')
