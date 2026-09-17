#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/boot/iso/dist/iso"
rm -rf "$DIST"
mkdir -p "$DIST/boot/grub" "$DIST/boot/spitfire" "$DIST/boot/jasper" "$DIST/boot/koronos" \
  "$DIST/EFI/BOOT" "$DIST/EFI/CHIMERA" "$DIST/chimera/docs" \
  "$DIST/chimera/manifests" "$DIST/chimera/toolchains/cpp" \
  "$DIST/chimera/applications" "$DIST/chimera/knowledge" \
  "$DIST/src" "$DIST/opt" "$DIST/install" "$DIST/drivers" \
  "$DIST/filesystems" "$DIST/packages" "$DIST/repositories" \
  "$DIST/man" "$DIST/games" "$DIST/wallets" "$DIST/ISO" "$DIST/checksums"
cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sf1_longmode.asm" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sf2_loader.cpp" "$ROOT/boot/spitfire/sf2_loader.h" "$ROOT/boot/spitfire/spitfire.ld" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sfu_uefi.c" "$ROOT/boot/spitfire/sfu_uefi.h" "$ROOT/boot/spitfire/sfu_uefi.ld" "$DIST/EFI/CHIMERA/"
cp "$ROOT/boot/spitfire/efi/README.md" "$DIST/EFI/CHIMERA/" 2>/dev/null || true
cp "$ROOT/boot/include/chimera/bootinfo.h" "$ROOT/boot/include/chimera/cpu_profile.h" "$ROOT/boot/include/chimera/boot_flags.h" "$DIST/boot/koronos/"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/grub/grub.cfg"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/jasper/"
[[ -f "$ROOT/boot/boot_protocol.json" ]] && cp "$ROOT/boot/boot_protocol.json" "$DIST/boot/"
[[ -f "$ROOT/boot/startup/boot_phase_manifest.json" ]] && cp "$ROOT/boot/startup/boot_phase_manifest.json" "$DIST/boot/"
[[ -f "$ROOT/boot/splash/support_footer.txt" ]] && cp "$ROOT/boot/splash/support_footer.txt" "$DIST/boot/"
if [[ -f "$ROOT/boot/kernel.bin" ]]; then cp "$ROOT/boot/kernel.bin" "$DIST/boot/kernel.bin"; fi
if [[ -f "$ROOT/boot/iso/dist/kernel.bin" ]]; then cp "$ROOT/boot/iso/dist/kernel.bin" "$DIST/boot/kernel.bin"; fi
if [[ -f "$ROOT/boot/iso/dist/chimera2os.elf" ]]; then cp "$ROOT/boot/iso/dist/chimera2os.elf" "$DIST/boot/koronos/koronos.elf"; fi
for d in include src kernel boot desktop network installer tools tests ai data cmake; do
  if [[ -d "$ROOT/$d" ]]; then mkdir -p "$DIST/src/$d"; cp -a "$ROOT/$d/." "$DIST/src/$d/"; fi
done
for d in nlp BizX BizXtreme general; do
  if [[ -d "$ROOT/opt/$d" ]]; then cp -a "$ROOT/opt/$d" "$DIST/opt/"; fi
done
[[ -d "$ROOT/appcenter" ]] && cp -a "$ROOT/appcenter" "$DIST/opt/appcenter"
[[ -d "$ROOT/games" ]] && cp -a "$ROOT/games/." "$DIST/games/"
[[ -d "$ROOT/wallets" ]] && cp -a "$ROOT/wallets/." "$DIST/wallets/"
for f in \
  "$ROOT/repositories/platform-manifest.json" \
  "$ROOT/drivers/driver-registry.json" \
  "$ROOT/filesystems/filesystem-registry.json" \
  "$ROOT/packages/package-manager-registry.json" \
  "$ROOT/compat/binary-format-registry.json" \
  "$ROOT/install/installer-contract.json" \
  "$ROOT/desktop/aurora/gates_menu.json"; do
  [[ -f "$f" ]] && cp "$f" "$DIST/chimera/manifests/"
done
[[ -d "$ROOT/toolchains/cpp" ]] && cp -a "$ROOT/toolchains/cpp/." "$DIST/chimera/toolchains/cpp/"
for f in "$ROOT/README.md" "$ROOT/docs/APPLICATION_ECOSYSTEM.md" "$ROOT/docs/MOBILE_PORTING_MATRIX.md" "$ROOT/docs/LEGAL_AND_PROVENANCE.md" "$ROOT/docs/INSTALLATION_AND_BOOT.md"; do
  [[ -f "$f" ]] && cp "$f" "$DIST/chimera/docs/"
done
cp "$ROOT/boot/iso/iso-layout.json" "$DIST/ISO/"
printf '%s\n' 'Chimera II OS structured source-first ISO' > "$DIST/chimera/README.txt"
printf '%s\n' 'Boot: Spit Fire / Jasper; kernel handoff: Koronos; media: ISO 9660 + El Torito.' >> "$DIST/chimera/README.txt"
printf '%s\n' 'Foreign drivers/binaries are metadata-only unless licensing, provenance and compatibility checks permit staging.' >> "$DIST/chimera/README.txt"
printf '%s\n' 'Support: created by Amer Abdullah Suleiman Hwitat | عامر الحويطات | Amman 11814/Jordan | amer.hwitat@proton.me' >> "$DIST/chimera/README.txt"
python3 "$ROOT/boot/iso/validate-iso.py" --tree "$DIST" --write-manifest "$DIST/checksums/SHA256SUMS"
