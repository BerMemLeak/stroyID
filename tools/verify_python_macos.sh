#!/bin/bash
# python.org documents this identity at https://www.python.org/downloads/
python_installer_identity_is_psf() {
    printf '%s\n' "$1" | /usr/bin/grep -Eq '^[[:space:]]*1\. Developer ID Installer: Python Software Foundation \(BMM5U3QVKW\)[[:space:]]*$'
}

verify_python_installer() {
    local signature
    signature="$(/usr/sbin/pkgutil --check-signature "$1")" || return
    printf '%s\n' "$signature"
    python_installer_identity_is_psf "$signature" || {
        echo 'Подпись установщика не принадлежит Python Software Foundation (BMM5U3QVKW).'
        return 1
    }
    /usr/sbin/spctl --assess --type install --verbose "$1"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    set -euo pipefail
    export LC_ALL=en_US.UTF-8
    [ "$#" -eq 1 ] || { echo 'Usage: verify_python_macos.sh installer.pkg'; exit 2; }
    verify_python_installer "$1"
fi
