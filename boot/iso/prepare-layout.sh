#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/boot/iso/dist/iso"
rm -rf "$DIST"
mkdir -p "$DIST/boot/spitfire" "$DIST/boot/jasper" "$DIST/boot/koronos" \
  "$DIST/EFI/BOOT" "$DIST/EFI/CHIMERA" "$DIST/chimera/docs" \
  "$DIST/chimera/manifests" "$DIST/chimera/toolchains/cpp" \
  "$DIST/chimera/applications" "$DIST/chimera/knowledge" "$DIST/src" "$DIST/checksums"

cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sf1_longmode.asm" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sf2_loader.cpp" "$ROOT/boot/spitfire/sf2_loader.h" "$ROOT/boot/spitfire/spitfire.ld" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sfu_uefi.c" "$ROOT/boot/spitfire/sfu_uefi.h" "$ROOT/boot/spitfire/sfu_uefi.ld" "$DIST/EFI/CHIMERA/"
cp "$ROOT/boot/spitfire/efi/README.md" "$DIST/EFI/CHIMERA/"
cp "$ROOT/kernel/include/chimera/bootinfo.h" "$DIST/boot/koronos/bootinfo.h" 2>/dev/null || true
cp "$ROOT/boot/include/chimera/bootinfo.h" "$ROOT/boot/include/chimera/cpu_profile.h" "$ROOT/boot/include/chimera/boot_flags.h" "$DIST/boot/koronos/"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/jasper/"

if [[ -f "$ROOT/boot/iso/dist/chimera2os.elf" ]]; then cp "$ROOT/boot/iso/dist/chimera2os.elf" "$DIST/boot/koronos/koronos.elf"; fi

for f in "$ROOT/README.md" "$ROOT/docs/APPLICATION_ECOSYSTEM.md" "$ROOT/docs/MOBILE_PORTING_MATRIX.md" "$ROOT/docs/LEGAL_AND_PROVENANCE.md" "$ROOT/docs/INSTALLATION_AND_BOOT.md"; do
  [[ -f "$f" ]] && cp "$f" "$DIST/chimera/docs/"
done
[[ -d "$ROOT/appcenter/catalog" ]] && cp -a "$ROOT/appcenter/catalog" "$DIST/chimera/applications/"
[[ -d "$ROOT/mobile/device-profiles" ]] && cp -a "$ROOT/mobile/device-profiles" "$DIST/chimera/applications/"
[[ -d "$ROOT/toolchains/cpp" ]] && cp -a "$ROOT/toolchains/cpp/." "$DIST/chimera/toolchains/cpp/"

printf 'Chimera II structured ISO staging tree\n' > "$DIST/chimera/README.txt"
printf 'Boot: Spit Fire / Jasper; kernel: Koronos bootstrap; media: ISO 9660 + El Torito.\n' >> "$DIST/chimera/README.txt"
printf 'Research-only CPU/ISA components remain explicitly experimental.\n' >> "$DIST/chimera/README.txt"

python3 "$ROOT/boot/iso/validate-iso.py" --tree "$DIST" --write-manifest "$DIST/checksums/SHA256SUMS"
