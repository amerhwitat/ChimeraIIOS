#!/usr/bin/env bash
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
