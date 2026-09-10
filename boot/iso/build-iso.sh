#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DIST="$ROOT/dist"
WORK="$ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST/iso/boot/grub" "$WORK"

CC=${CC:-gcc}
LD=${LD:-ld}

$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -c "$ROOT/multiboot2.S" -o "$WORK/multiboot2.o"
$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -c "$ROOT/boot.c" -o "$WORK/boot.o"
$LD -m elf_i386 -T "$ROOT/linker.ld" -o "$WORK/chimera2os.elf" "$WORK/multiboot2.o" "$WORK/boot.o"
cp "$WORK/chimera2os.elf" "$DIST/iso/boot/chimera2os.elf"
cp "$ROOT/grub.cfg" "$DIST/iso/boot/grub/grub.cfg"
grub-mkrescue -o "$DIST/chimera2os-bootstrap.iso" "$DIST/iso"
printf 'ISO: %s\n' "$DIST/chimera2os-bootstrap.iso"
