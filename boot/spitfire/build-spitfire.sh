#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/boot/iso/dist/bootloaders}"
KERNEL="${2:-$ROOT/build/koronos/x86_64/koronos.elf}"
mkdir -p "$OUT"
command -v nasm >/dev/null || { echo "error: nasm is required" >&2; exit 1; }
command -v g++ >/dev/null || { echo "error: g++ is required" >&2; exit 1; }
command -v ld >/dev/null || { echo "error: ld is required" >&2; exit 1; }

nasm -f bin "$ROOT/boot/spitfire/sf0_mbr.asm" -o "$OUT/spitfire-sf0-mbr.bin"
[[ "$(stat -c%s "$OUT/spitfire-sf0-mbr.bin")" -eq 512 ]] || { echo "error: SF0 MBR is not 512 bytes" >&2; exit 1; }

nasm -f elf64 "$ROOT/boot/spitfire/sf1_longmode.asm" -o "$OUT/spitfire-sf1-longmode.o"
g++ -ffreestanding -fno-exceptions -fno-rtti -fno-stack-protector -fno-pic -fno-pie -mno-red-zone -mno-sse -mno-mmx -nostdinc++ -I"$ROOT/kernel/include" -c "$ROOT/boot/spitfire/sf2_loader.cpp" -o "$OUT/spitfire-sf2-loader.o"
ld -nostdlib -z max-page-size=0x1000 --build-id=none -T "$ROOT/boot/spitfire/spitfire.ld" "$OUT/spitfire-sf1-longmode.o" "$OUT/spitfire-sf2-loader.o" -o "$OUT/spitfire-stage2.bin"

STAGE_SECTORS=$(( ($(stat -c%s "$OUT/spitfire-stage2.bin") + 511) / 512 ))
if (( STAGE_SECTORS > 127 )); then
  echo "error: Spit Fire stage2 is ${STAGE_SECTORS} sectors; refusing an oversized single BIOS EDD transfer." >&2
  exit 1
fi
python3 - "$OUT/spitfire-sf0-mbr.bin" "$STAGE_SECTORS" <<'PY'
import pathlib, struct, sys
p = pathlib.Path(sys.argv[1])
n = int(sys.argv[2])
b = bytearray(p.read_bytes())
needle = b"\x10\x00\x1f\x00\x00\x7e"
i = b.find(needle)
if i < 0:
    raise SystemExit("DAP signature not found in SF0")
b[i+2:i+4] = struct.pack("<H", n)
p.write_bytes(b)
PY
cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$OUT/"
cp "$ROOT/boot/spitfire/sf1_longmode.asm" "$OUT/"
printf '%s\n' "Spit Fire native BIOS artifacts:" > "$OUT/BUILD-MANIFEST.txt"
printf '%s\n' "SF0: 512-byte MBR stage; SF1+SF2: linked stage2 (${STAGE_SECTORS} sectors)." >> "$OUT/BUILD-MANIFEST.txt"
printf '%s\n' "Kernel handoff contract: stage2 produces koronos_boot_context; GRUB is the canonical ISO kernel loader." >> "$OUT/BUILD-MANIFEST.txt"
sha256sum "$OUT"/spitfire-sf0-mbr.bin "$OUT"/spitfire-stage2.bin "$OUT"/spitfire-sf1-longmode.o "$OUT"/spitfire-sf2-loader.o > "$OUT/SHA256SUMS"
