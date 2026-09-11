#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ISO_ROOT="$ROOT/boot/iso"
DIST="$ISO_ROOT/dist"
WORK="$ISO_ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK"
CC=${CC:-gcc}; LD=${LD:-ld}
printf '%s\n' '[1/5] Build Multiboot2 bootstrap kernel'
$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -I"$ROOT/boot/include" -c "$ISO_ROOT/multiboot2.S" -o "$WORK/multiboot2.o"
$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -I"$ROOT/boot/include" -c "$ISO_ROOT/boot.c" -o "$WORK/boot.o"
$LD -m elf_i386 -T "$ISO_ROOT/linker.ld" -o "$DIST/chimera2os.elf" "$WORK/multiboot2.o" "$WORK/boot.o"
printf '%s\n' '[2/5] Prepare structured media tree'
"$ISO_ROOT/prepare-layout.sh"
cp "$DIST/chimera2os.elf" "$ISO_ROOT/dist/iso/boot/koronos/koronos.elf"
cp "$DIST/chimera2os.elf" "$ISO_ROOT/dist/iso/boot/chimera2os.elf"
cp "$ISO_ROOT/iso-layout.json" "$ISO_ROOT/dist/iso/chimera/manifests/iso-layout.json"
printf '%s\n' '[3/5] Add boot configuration'
mkdir -p "$ISO_ROOT/dist/iso/boot/grub"
cp "$ISO_ROOT/grub.cfg" "$ISO_ROOT/dist/iso/boot/grub.cfg"
cp "$ISO_ROOT/grub.cfg" "$ISO_ROOT/dist/iso/boot/grub/grub.cfg"
printf '%s\n' '[4/5] Validate final staging tree'
python3 "$ISO_ROOT/validate-iso.py" --tree "$ISO_ROOT/dist/iso" --write-manifest "$ISO_ROOT/dist/iso/checksums/SHA256SUMS"
printf '%s\n' '[5/5] Master ISO 9660 / El Torito image'
if command -v grub-mkrescue >/dev/null 2>&1; then
  grub-mkrescue -o "$DIST/chimera2os-bootstrap.iso" "$DIST/iso"
elif command -v xorriso >/dev/null 2>&1; then
  echo 'xorriso found but grub-mkrescue is missing; install GRUB2 EFI/BIOS modules for hybrid authoring.' >&2
  exit 2
else
  echo 'No ISO authoring backend found: install grub-mkrescue/GRUB2 and xorriso.' >&2
  exit 2
fi
sha256sum "$DIST/chimera2os-bootstrap.iso" | tee "$DIST/chimera2os-bootstrap.iso.sha256"
printf 'ISO: %s\nStructured tree: %s\n' "$DIST/chimera2os-bootstrap.iso" "$DIST/iso"
