#!/bin/bash
# Alias for the complete local setup, test and .app build workflow.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /bin/bash "$ROOT/setup_and_build_macos.command" "$@"
