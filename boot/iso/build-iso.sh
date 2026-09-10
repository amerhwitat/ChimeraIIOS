#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
DIST="$ROOT/dist"
WORK="$ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST/iso/boot/grub" "$DIST/iso/chimera/appcenter" "$DIST/iso/chimera/mobile" "$DIST/iso/chimera/docs" "$DIST/iso/chimera/manifests" "$WORK"

CC=${CC:-gcc}
LD=${LD:-ld}

$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -c "$ROOT/multiboot2.S" -o "$WORK/multiboot2.o"
$CC -m32 -ffreestanding -fno-pie -fno-stack-protector -fno-builtin -c "$ROOT/boot.c" -o "$WORK/boot.o"
$LD -m elf_i386 -T "$ROOT/linker.ld" -o "$WORK/chimera2os.elf" "$WORK/multiboot2.o" "$WORK/boot.o"
cp "$WORK/chimera2os.elf" "$DIST/iso/boot/chimera2os.elf"
cp "$ROOT/grub.cfg" "$DIST/iso/boot/grub/grub.cfg"

cp -a "$REPO/appcenter/catalog" "$DIST/iso/chimera/appcenter/"
cp -a "$REPO/appcenter/providers" "$DIST/iso/chimera/appcenter/"
cp -a "$REPO/appcenter/schema" "$DIST/iso/chimera/appcenter/"
cp -a "$REPO/appcenter/cli" "$DIST/iso/chimera/appcenter/"
cp -a "$REPO/mobile/device-profiles" "$DIST/iso/chimera/mobile/"
cp "$REPO/mobile/device-profile.schema.json" "$DIST/iso/chimera/mobile/"
cp "$REPO/iso/manifests/core-packages.txt" "$DIST/iso/chimera/manifests/"
cp "$REPO/iso/manifests/application-catalog.txt" "$DIST/iso/chimera/manifests/"
cp "$REPO/docs/APPLICATION_ECOSYSTEM.md" "$DIST/iso/chimera/docs/"
cp "$REPO/docs/MOBILE_PORTING_MATRIX.md" "$DIST/iso/chimera/docs/"
cp "$REPO/docs/LEGAL_AND_PROVENANCE.md" "$DIST/iso/chimera/docs/"

printf 'Chimera II application catalog bundled into ISO.\n' > "$DIST/iso/chimera/README.txt"
printf 'Core open-source components are bundled; proprietary applications use official distribution adapters.\n' >> "$DIST/iso/chimera/README.txt"

grub-mkrescue -o "$DIST/chimera2os-bootstrap.iso" "$DIST/iso"
printf 'ISO: %s\n' "$DIST/chimera2os-bootstrap.iso"
