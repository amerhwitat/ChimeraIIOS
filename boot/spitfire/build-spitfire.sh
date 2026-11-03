#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: boot/spitfire/build-spitfire.sh

Usage:
  boot/spitfire/build-spitfire.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/boot/iso/dist/bootloaders}"
KERNEL="${2:-$ROOT/build/koronos/x86_64/koronos.elf}"
mkdir -p "$OUT"
[[ -s "$KERNEL" ]] || { echo "error: validated Koronos kernel ELF is required: $KERNEL" >&2; exit 1; }
python3 - "$KERNEL" <<'PY'
import pathlib, struct, sys
p = pathlib.Path(sys.argv[1])
d = p.read_bytes()
if len(d) < 64 or d[:4] != b"\\x7fELF" or d[4] != 2 or d[5] != 1:
    raise SystemExit("Spit Fire requires a little-endian ELF64 Koronos kernel")
if struct.unpack_from("<H", d, 18)[0] != 62:
    raise SystemExit("Spit Fire requires an x86-64 Koronos kernel")
magic = 0xE85250D6
valid = any(
    struct.unpack_from("<I", d, off)[0] == magic
    and struct.unpack_from("<I", d, off + 4)[0] == 0
    and struct.unpack_from("<I", d, off + 8)[0] >= 16
    and off + struct.unpack_from("<I", d, off + 8)[0] <= len(d)
    and ((magic + struct.unpack_from("<III", d, off + 4)[0]
          + struct.unpack_from("<III", d, off + 4)[1]
          + struct.unpack_from("<III", d, off + 4)[2]) & 0xffffffff) == 0
    for off in range(0, min(len(d), 32768) - 16, 8)
)
if not valid:
    raise SystemExit("Spit Fire requires a valid Multiboot2 header in the Koronos ELF")
PY
sha256sum "$KERNEL" | awk '{print $1 "  koronos.elf"}' > "$OUT/koronos.elf.sha256"
command -v nasm >/dev/null || { echo "error: nasm is required" >&2; exit 1; }
command -v g++ >/dev/null || { echo "error: g++ is required" >&2; exit 1; }
command -v ld >/dev/null || { echo "error: ld is required" >&2; exit 1; }
command -v nm >/dev/null || { echo "error: nm is required" >&2; exit 1; }

nasm -f bin "$ROOT/boot/spitfire/sf0_mbr.asm" -o "$OUT/spitfire-sf0-mbr.bin"
[[ "$(stat -c%s "$OUT/spitfire-sf0-mbr.bin")" -eq 512 ]] || { echo "error: SF0 MBR is not 512 bytes" >&2; exit 1; }

nasm -f elf64 "$ROOT/boot/spitfire/sf1_longmode.asm" -o "$OUT/spitfire-sf1-longmode.o"
# sf1_longmode.asm is linked with ENTRY(start); verify that NASM exported
# start instead of leaving it local. Without this check ld.bfd silently falls
# back to the default address and emits "cannot find entry symbol start".
nm -g "$OUT/spitfire-sf1-longmode.o" | grep -Eq '[[:space:]]T[[:space:]]start$' || {
  echo "error: Spit Fire SF1 does not export global start entry symbol" >&2
  exit 1
}
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
sha256sum "$OUT"/spitfire-sf0-mbr.bin "$OUT"/spitfire-stage2.bin "$OUT"/spitfire-sf1-longmode.o "$OUT"/spitfire-sf2-loader.o "$OUT"/koronos.elf.sha256 > "$OUT/SHA256SUMS"
