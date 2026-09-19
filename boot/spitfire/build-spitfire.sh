#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/boot/iso/dist/bootloaders}"
mkdir -p "$OUT"
command -v nasm >/dev/null || { echo 'error: nasm is required' >&2; exit 1; }

echo '[Spit Fire] Assemble BIOS MBR stage'
nasm -f bin "$ROOT/boot/spitfire/sf0_mbr.asm" -o "$OUT/spitfire-sf0-mbr.bin"
[[ $(stat -c%s "$OUT/spitfire-sf0-mbr.bin") -eq 512 ]] || { echo 'error: SF0 MBR is not 512 bytes' >&2; exit 1; }

# SF1 contains an explicit 64-bit C++ handoff symbol, so preserve it as an ELF
# object rather than pretending it is a self-contained flat binary.
echo '[Spit Fire] Assemble long-mode handoff object'
nasm -f elf64 "$ROOT/boot/spitfire/sf1_longmode.asm" -o "$OUT/spitfire-sf1-longmode.o"

cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$ROOT/boot/spitfire/sf1_longmode.asm" "$OUT/"
printf '%s\n' 'Spit Fire bootloader artifacts assembled successfully.' > "$OUT/BUILD-MANIFEST.txt"
printf '%s\n' 'SF0: raw BIOS MBR stage; SF1: ELF64 long-mode handoff object.' >> "$OUT/BUILD-MANIFEST.txt"
sha256sum "$OUT"/spitfire-sf0-mbr.bin "$OUT"/spitfire-sf1-longmode.o > "$OUT/SHA256SUMS"
