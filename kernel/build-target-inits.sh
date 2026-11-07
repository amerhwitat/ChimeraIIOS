#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "\${1:-}" == "--help" || "\${1:-}" == "-h" ]]; then
  cat <<'HELP'
Build the native x86-64 ring-3 init images used by Koronos Live, Installer and Recovery.

Usage:
  kernel/build-target-inits.sh

Outputs:
  build/koronos/x86_64/target-init-live.elf
  build/koronos/x86_64/target-init-installer.elf
  build/koronos/x86_64/target-init-recovery.elf

These are real freestanding ET_EXEC ELF payloads for the current x86-64 Koronos
syscall ABI. They are not Linux initramfs binaries or other-architecture ports.
HELP
  exit 0
fi

ROOT="$(cd -- "$(dirname -- "\${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/koronos/x86_64"
CC="\${CC:-gcc}"
LD="\${LD:-ld}"
READELF="\${READELF:-readelf}"
mkdir -p "$OUT"
command -v "$CC" >/dev/null 2>&1 || { echo "ERROR: C compiler missing: $CC" >&2; exit 2; }
command -v "$LD" >/dev/null 2>&1 || { echo "ERROR: linker missing: $LD" >&2; exit 2; }
command -v "$READELF" >/dev/null 2>&1 || { echo "ERROR: readelf is required to validate target init ELF files" >&2; exit 2; }

CFLAGS=(
  -std=c11 -O2 -Wall -Wextra -Werror
  -ffreestanding -fno-builtin -fno-stack-protector
  -fno-pic -fno-pie -fno-asynchronous-unwind-tables
  -m64 -mno-red-zone -mcmodel=large
  -nostdlib -nostdinc
  -I"$ROOT/kernel/targets"
)
for target in live installer recovery; do
  source="$ROOT/kernel/targets/\${target}_init.c"
  object="$OUT/target-init-\${target}.o"
  image="$OUT/target-init-\${target}.elf"
  [[ -s "$source" ]] || { echo "ERROR: target init source missing: $source" >&2; exit 2; }
  echo "[TARGET] Building $target ring-3 init"
  "$CC" "\${CFLAGS[@]}" -DCHIMERA_TARGET_NAME="\"$target\"" -c "$source" -o "$object"
  "$LD" -m elf_x86_64 -nostdlib -z max-page-size=0x1000 --build-id=none \
    -T "$ROOT/kernel/targets/target_init.ld" "$object" -o "$image"
  "$READELF" -h "$image" | grep -Eq 'Class:[[:space:]]+ELF64' || {
    echo "ERROR: $image is not ELF64" >&2; exit 2; }
  "$READELF" -h "$image" | grep -Eq 'Type:[[:space:]]+EXEC' || {
    echo "ERROR: $image is not ET_EXEC" >&2; exit 2; }
  "$READELF" -h "$image" | grep -Eq 'Machine:[[:space:]]+Advanced Micro Devices X86-64' || {
    echo "ERROR: $image is not x86-64" >&2; exit 2; }
  if "$READELF" -l "$image" | grep -q 'INTERP'; then
    echo "ERROR: $image unexpectedly requires a dynamic interpreter" >&2; exit 2
  fi
  [[ -s "$image" ]] || { echo "ERROR: empty target init image: $image" >&2; exit 2; }
  echo "[TARGET] VERIFIED $image"
done
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
for name in ("live","installer","recovery"):
    p=root/f"target-init-{name}.elf"
    if not p.is_file() or p.stat().st_size < 512:
        raise SystemExit(f"target init missing or implausibly small: {p}")
print("All three target init ELFs exist and passed ELF header validation.")
PY
