#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/tests/test-koronos-progress.sh

Usage:
  tools/tests/test-koronos-progress.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CHIMERA_PROGRESS_DIR="$TMP" bash "$ROOT/system/boot/koronos-progress.sh" set 42 devices 'Device discovery'
out="$(CHIMERA_PROGRESS_DIR="$TMP" bash "$ROOT/system/boot/koronos-progress.sh" get)"
grep -q '^percent=42$' <<<"$out"
grep -q '^phase=devices$' <<<"$out"
grep -q '^message=Device discovery$' <<<"$out"
if CHIMERA_PROGRESS_DIR="$TMP" bash "$ROOT/system/boot/koronos-progress.sh" set 101 devices bad 2>/dev/null; then exit 1; fi
printf 'PASS: Koronos progress contract\n'
