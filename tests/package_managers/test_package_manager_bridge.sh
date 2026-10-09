#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLI="$ROOT/tools/chimera-package-manager.sh"
bash -n "$CLI"
help="$(bash "$CLI" --help)"
grep -q 'homebrew' <<<"$help"; grep -q 'flatpak' <<<"$help"; grep -q 'snap' <<<"$help"
status="$(bash "$CLI" status)"
grep -q '^apt ' <<<"$status"
if bash "$CLI" bogus >/dev/null 2>&1; then echo "Unknown action unexpectedly succeeded" >&2; exit 1; fi
if CHIMERA_PKG_MANAGER=not-a-manager bash "$CLI" list >/dev/null 2>&1; then echo "Unknown provider unexpectedly succeeded" >&2; exit 1; fi
python3 -m py_compile "$ROOT/desktop/aurora/package_manager_panel.py"
python3 -m json.tool "$ROOT/appcenter/catalog/package-managers.json" >/dev/null
printf '%s\n' 'Package manager bridge checks passed.'
