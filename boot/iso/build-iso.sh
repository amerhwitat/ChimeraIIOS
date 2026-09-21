#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ISO_ROOT="$ROOT/boot/iso"
DIST="$ISO_ROOT/dist"
WORK="$ISO_ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK"
CC=${CC:-gcc}; LD=${LD:-ld}
printf '%s\n' '[1/7] Build Multiboot2 Koronos x86_64 kernel payload'
"$ROOT/kernel/build-koronos.sh"
KORONOS_ELF="$ROOT/build/koronos/x86_64/koronos.elf"
test -s "$KORONOS_ELF"
if command -v grub-file >/dev/null 2>&1; then
  grub-file --is-x86-multiboot2 "$KORONOS_ELF"
else
  echo 'grub-file is required to validate the Multiboot2 kernel payload.' >&2
  exit 2
fi
cp "$KORONOS_ELF" "$DIST/chimera2os.elf"
cp "$KORONOS_ELF" "$DIST/kernel.bin"
printf '%s\n' '[2/7] Prepare structured media tree'
"$ISO_ROOT/prepare-layout.sh"
printf '%s\n' '[3/7] Assemble Spit Fire BIOS bootloader stages with NASM'
"$ROOT/boot/spitfire/build-spitfire.sh" "$DIST/bootloaders"
cp "$KORONOS_ELF" "$ISO_ROOT/dist/iso/boot/koronos/koronos.elf"
cp "$KORONOS_ELF" "$ISO_ROOT/dist/iso/boot/kernel.bin"
cp "$DIST/chimera2os.elf" "$ISO_ROOT/dist/iso/boot/chimera2os.elf"
cp "$DIST/bootloaders/spitfire-sf0-mbr.bin" "$ISO_ROOT/dist/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-sf1-longmode.o" "$ISO_ROOT/dist/iso/boot/spitfire/"
cp "$ISO_ROOT/iso-layout.json" "$ISO_ROOT/dist/iso/chimera/manifests/iso-layout.json"
printf '%s\n' '[4/7] Add GRUB2 boot configuration'
mkdir -p "$ISO_ROOT/dist/iso/boot/grub"
cp "$ISO_ROOT/grub.cfg" "$ISO_ROOT/dist/iso/boot/grub.cfg"
cp "$ISO_ROOT/grub.cfg" "$ISO_ROOT/dist/iso/boot/grub/grub.cfg"
printf '%s\n' '[5/7] Validate ISA and final staging tree'
python3 "$ROOT/tools/isa/validate-isa.py"
python3 "$ISO_ROOT/validate-iso.py" --tree "$ISO_ROOT/dist/iso" --write-manifest "$ISO_ROOT/dist/iso/checksums/SHA256SUMS"
printf '%s\n' '[6/7] Master ISO 9660 / El Torito hybrid image'
if command -v grub-mkrescue >/dev/null 2>&1; then
  grub-mkrescue -o "$DIST/chimera2os-bootstrap.iso" "$DIST/iso"
elif command -v xorriso >/dev/null 2>&1; then
  echo 'xorriso found but grub-mkrescue is missing; install GRUB2 BIOS/UEFI modules for hybrid authoring.' >&2
  exit 2
else
  echo 'No ISO authoring backend found: install grub-mkrescue/GRUB2 and xorriso.' >&2
  exit 2
fi
cp "$DIST/chimera2os-bootstrap.iso" "$DIST/output.iso"
sha256sum "$DIST/chimera2os-bootstrap.iso" | tee "$DIST/chimera2os-bootstrap.iso.sha256"
sha256sum "$DIST/output.iso" | tee "$DIST/output.iso.sha256"
printf '%s\n' '[7/7] ISO boot metadata inspection'
if command -v xorriso >/dev/null 2>&1; then
  xorriso -indev "$DIST/output.iso" -report_el_torito plain -report_system_area plain | tee "$DIST/ISO-BOOT-REPORT.txt"
fi
printf 'ISO: %s\nStructured tree: %s\nBootloader artifacts: %s\n' "$DIST/output.iso" "$DIST/iso" "$DIST/bootloaders"
