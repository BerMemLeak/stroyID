#!/bin/bash
# Full native Apple Silicon build. Does not modify the Windows environment.
set -Eeuo pipefail
export LC_ALL=en_US.UTF-8
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p logs
LOG="$ROOT/logs/build-macos-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
finish() {
    status=$?
    if [ "$status" -ne 0 ]; then
        printf '\nСборка остановлена. Журнал: %s\n' "$LOG"
        if [ -t 0 ]; then read -r -p 'Нажмите Enter для закрытия.' _reply; fi
    fi
}
trap finish EXIT
NO_LAUNCH=0
for arg in "$@"; do
    case "$arg" in
        --no-launch) NO_LAUNCH=1 ;;
        *) printf 'Неизвестный параметр: %s\n' "$arg"; exit 2 ;;
    esac
done
[ "$(uname -s)" = Darwin ] || { echo 'Запустите этот скрипт на macOS.'; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo 'Нужен Apple Silicon. Откройте Terminal без режима Rosetta.'; exit 1; }
MAC_MAJOR="$(sw_vers -productVersion | cut -d. -f1)"
[ "$MAC_MAJOR" -ge 13 ] || { echo 'Требуется macOS 13 или новее.'; exit 1; }
CHECK='import platform,sys; assert platform.machine()=="arm64" and sys.version_info[:2] in ((3,12),(3,13)); print(sys.executable)'
BUILD_PYTHON=''
for candidate in "${STROYID_BUILD_PYTHON:-}" "$(command -v python3.13 || true)" "$(command -v python3.12 || true)" \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
    /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12; do
    if [ -n "$candidate" ] && [ -x "$candidate" ] && "$candidate" -c "$CHECK" >/dev/null 2>&1; then
        BUILD_PYTHON="$candidate"; break
    fi
done
if [ -z "$BUILD_PYTHON" ]; then
    echo 'Нужен Python ARM64. Загружается официальный установщик Python 3.13.16.'
    PKG="$ROOT/logs/python-3.13.16-macos11.pkg"
    /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 --retry 3 \
        https://www.python.org/ftp/python/3.13.16/python-3.13.16-macos11.pkg -o "$PKG"
    SIGNATURE="$(/usr/sbin/pkgutil --check-signature "$PKG")"
    printf '%s\n' "$SIGNATURE"
    printf '%s\n' "$SIGNATURE" | /usr/bin/grep -q 'Python Software Foundation (DJ3H93M7VJ)' || { echo 'Подпись Python Software Foundation не подтверждена.'; exit 1; }
    /usr/sbin/spctl --assess --type install --verbose "$PKG"
    echo 'Завершите установку Python в открывшемся системном окне и закройте Installer. Затем сборка продолжится.'
    /usr/bin/open -W -a Installer "$PKG"
    BUILD_PYTHON=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13
    "$BUILD_PYTHON" -c "$CHECK"
fi
echo "Python: $BUILD_PYTHON"
VENV="$ROOT/.venv-macos"
if [ ! -x "$VENV/bin/python" ]; then "$BUILD_PYTHON" -m venv "$VENV"; fi
"$VENV/bin/python" -c "$CHECK" || { echo 'Окружение .venv-macos не подходит. Переименуйте его и повторите сборку.'; exit 1; }
"$VENV/bin/python" -m pip install -r requirements-build.txt
"$VENV/bin/python" tools/build_release.py
printf '\nГотово: release/StroyID-macOS-arm64.zip и release/StroyID-macOS-arm64.dmg\n'
if [ "$NO_LAUNCH" -eq 0 ]; then /usr/bin/open "$ROOT/dist-macos/StroyID.app"; fi
