#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HELPER="$SCRIPT_DIR/tools/wsl/map-windows-drives.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/mnt/c/Users/Test" "$TMP/mnt/d/Projects" "$TMP/drive"
export CHIMERA_FORCE_WSL=1
export CHIMERA_WSL_MNT_ROOT="$TMP/mnt"
export CHIMERA_WINDOWS_DRIVE_ROOT="$TMP/drive"
export CHIMERA_WSL_DRIVE_ALLOW_UNVERIFIED=1

bash -n "$HELPER"
bash "$HELPER" >"$TMP/first.log"
[[ -L "$TMP/drive/C" ]]
[[ -L "$TMP/drive/D" ]]
[[ "$(readlink -f "$TMP/drive/C")" == "$(readlink -f "$TMP/mnt/c")" ]]
[[ "$(readlink -f "$TMP/drive/D")" == "$(readlink -f "$TMP/mnt/d")" ]]

# Repeated execution must be idempotent.
bash "$HELPER" >"$TMP/second.log"
grep -q "already mapped" "$TMP/second.log"

# Dry-run must not create a root or aliases.
export CHIMERA_WINDOWS_DRIVE_ROOT="$TMP/dry-run"
export CHIMERA_WSL_DRIVE_DRY_RUN=1
bash "$HELPER" >"$TMP/dry.log"
[[ ! -e "$TMP/dry-run" ]]
grep -q "would map" "$TMP/dry.log"
unset CHIMERA_WSL_DRIVE_DRY_RUN

# Existing user data must never be replaced.
export CHIMERA_WINDOWS_DRIVE_ROOT="$TMP/drive"
printf 'keep-me\n' >"$TMP/drive/E"
mkdir -p "$TMP/mnt/e"
bash "$HELPER" >"$TMP/collision.log" 2>&1
[[ -f "$TMP/drive/E" ]]
grep -q "keep-me" "$TMP/drive/E"
grep -q "refusing to overwrite existing path" "$TMP/collision.log"

# A non-WSL invocation must fail closed without creating the destination.
unset CHIMERA_FORCE_WSL WSL_INTEROP
export CHIMERA_WINDOWS_DRIVE_ROOT="$TMP/non-wsl"
if bash "$HELPER" >"$TMP/non-wsl.log" 2>&1; then
  echo "ERROR: non-WSL invocation unexpectedly succeeded" >&2
  exit 1
fi
[[ ! -e "$TMP/non-wsl" ]]

echo "[wsl-drive] all mapping, idempotence, dry-run, collision and non-WSL tests passed"
