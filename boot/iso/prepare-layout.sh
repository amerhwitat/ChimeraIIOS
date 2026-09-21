#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/boot/iso/dist/iso"
rm -rf "$DIST"
if [[ -x "$ROOT/tools/build-desktop-binaries.sh" ]]; then "$ROOT/tools/build-desktop-binaries.sh"; fi
mkdir -p "$DIST/chimera/hardware" "$DIST/chimera/security" "$DIST/chimera/system" "$DIST/boot/grub" "$DIST/boot/spitfire" "$DIST/boot/jasper" "$DIST/boot/koronos" \
  "$DIST/EFI/BOOT" "$DIST/EFI/CHIMERA" "$DIST/chimera/docs" \
  "$DIST/chimera/manifests" "$DIST/chimera/toolchains/cpp" \
  "$DIST/chimera/applications" "$DIST/chimera/knowledge" \
  "$DIST/src" "$DIST/opt" "$DIST/install" "$DIST/drivers" \
  "$DIST/filesystems" "$DIST/packages" "$DIST/repositories" \
  "$DIST/man" "$DIST/games" "$DIST/wallets" "$DIST/ISO" "$DIST/checksums"
cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$ROOT/boot/spitfire/sf1_longmode.asm" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sf2_loader.cpp" "$ROOT/boot/spitfire/sf2_loader.h" "$ROOT/boot/spitfire/spitfire.ld" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sfu_uefi.c" "$ROOT/boot/spitfire/sfu_uefi.h" "$ROOT/boot/spitfire/sfu_uefi.ld" "$DIST/EFI/CHIMERA/"
cp "$ROOT/boot/spitfire/efi/README.md" "$DIST/EFI/CHIMERA/" 2>/dev/null || true
cp "$ROOT/boot/include/chimera/bootinfo.h" "$ROOT/boot/include/chimera/cpu_profile.h" "$ROOT/boot/include/chimera/boot_flags.h" "$DIST/boot/koronos/"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/grub/grub.cfg"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/jasper/"
[[ -f "$ROOT/boot/boot_protocol.json" ]] && cp "$ROOT/boot/boot_protocol.json" "$DIST/boot/"
[[ -f "$ROOT/boot/startup/boot_phase_manifest.json" ]] && cp "$ROOT/boot/startup/boot_phase_manifest.json" "$DIST/boot/"
[[ -f "$ROOT/boot/splash/support_footer.txt" ]] && cp "$ROOT/boot/splash/support_footer.txt" "$DIST/boot/"
[[ -f "$ROOT/boot/kernel.bin" ]] && cp "$ROOT/boot/kernel.bin" "$DIST/boot/kernel.bin"
[[ -f "$ROOT/boot/iso/dist/kernel.bin" ]] && cp "$ROOT/boot/iso/dist/kernel.bin" "$DIST/boot/kernel.bin"
[[ -f "$ROOT/boot/iso/dist/chimera2os.elf" ]] && cp "$ROOT/boot/iso/dist/chimera2os.elf" "$DIST/boot/koronos/koronos.elf"
if [[ -d "$ROOT/build/desktop" ]]; then
  mkdir -p "$DIST/bin/desktop"
  cp -a "$ROOT/build/desktop/." "$DIST/bin/desktop/"
fi
for d in include src kernel boot desktop network installer tools tests ai data cmake; do
  if [[ -d "$ROOT/$d" ]]; then mkdir -p "$DIST/src/$d"; cp -a "$ROOT/$d/." "$DIST/src/$d/"; fi
done
if [[ -f "$ROOT/ISA.csv" ]]; then
  cp "$ROOT/ISA.csv" "$DIST/src/ISA.csv"
fi
if [[ -f "$ROOT/tools/isa/validate-isa.py" ]]; then
  mkdir -p "$DIST/src/tools/isa"
  cp "$ROOT/tools/isa/validate-isa.py" "$DIST/src/tools/isa/"
fi
for d in nlp BizX BizXtreme general; do
  if [[ -d "$ROOT/opt/$d" ]]; then cp -a "$ROOT/opt/$d" "$DIST/opt/"; fi
done
[[ -d "$ROOT/appcenter" ]] && cp -a "$ROOT/appcenter" "$DIST/opt/appcenter"
[[ -d "$ROOT/drivers" ]] && cp -a "$ROOT/drivers/." "$DIST/drivers/"
[[ -d "$ROOT/hardware" ]] && cp -a "$ROOT/hardware/." "$DIST/chimera/hardware/"
[[ -d "$ROOT/security" ]] && cp -a "$ROOT/security/." "$DIST/chimera/security/"
[[ -d "$ROOT/system" ]] && cp -a "$ROOT/system/." "$DIST/chimera/system/"
if [[ -f "$ROOT/desktop/aurora/assets/aurora-wayland-glass.png" ]]; then
  mkdir -p "$DIST/boot/grub" "$DIST/usr/share/chimera/aurora"
  cp "$ROOT/desktop/aurora/assets/aurora-wayland-glass.png" "$DIST/boot/grub/aurora-wayland-glass.png"
  cp "$ROOT/desktop/aurora/assets/aurora-wayland-glass.png" "$DIST/usr/share/chimera/aurora/aurora-wayland-glass.png"
fi
[[ -d "$ROOT/games" ]] && cp -a "$ROOT/games/." "$DIST/games/"
[[ -d "$ROOT/wallets" ]] && cp -a "$ROOT/wallets/." "$DIST/wallets/"
for f in \
  "$ROOT/repositories/platform-manifest.json" \
  "$ROOT/drivers/driver-registry.json" \
  "$ROOT/filesystems/filesystem-registry.json" \
  "$ROOT/packages/package-manager-registry.json" \
  "$ROOT/compat/binary-format-registry.json" \
  "$ROOT/install/installer-contract.json" \
  "$ROOT/desktop/aurora/gates_menu.json" \
  "$ROOT/appcenter/catalog/external-integrations.json"; do
  [[ -f "$f" ]] && cp "$f" "$DIST/chimera/manifests/"
done
[[ -d "$ROOT/toolchains/cpp" ]] && cp -a "$ROOT/toolchains/cpp/." "$DIST/chimera/toolchains/cpp/"
[[ -f "$ROOT/repositories/portfolio-integration.json" ]] && cp "$ROOT/repositories/portfolio-integration.json" "$DIST/chimera/manifests/"
[[ -f "$ROOT/repositories/reference-document-import.json" ]] && cp "$ROOT/repositories/reference-document-import.json" "$DIST/chimera/manifests/"
[[ -f "$ROOT/repositories/isa-sources.json" ]] && cp "$ROOT/repositories/isa-sources.json" "$DIST/chimera/manifests/"
# Optional CI/local portfolio build output. This is populated by tools/portfolio/build_portfolio.py.
if [[ -d "$ROOT/boot/iso/portfolio-build" ]]; then
  mkdir -p "$DIST/src/portfolio" "$DIST/bin/portfolio" "$DIST/docs/references"
  [[ -d "$ROOT/boot/iso/portfolio-build/src" ]] && cp -a "$ROOT/boot/iso/portfolio-build/src/." "$DIST/src/portfolio/"
  [[ -d "$ROOT/boot/iso/portfolio-build/binaries" ]] && cp -a "$ROOT/boot/iso/portfolio-build/binaries/." "$DIST/bin/portfolio/"
  [[ -d "$ROOT/boot/iso/portfolio-build/docs/references" ]] && cp -a "$ROOT/boot/iso/portfolio-build/docs/references/." "$DIST/docs/references/"
  [[ -f "$ROOT/boot/iso/portfolio-build/portfolio-build-report.json" ]] && cp "$ROOT/boot/iso/portfolio-build/portfolio-build-report.json" "$DIST/chimera/manifests/"
fi
for f in "$ROOT/README.md" "$ROOT/docs/APPLICATION_ECOSYSTEM.md" "$ROOT/docs/MOBILE_PORTING_MATRIX.md" "$ROOT/docs/LEGAL_AND_PROVENANCE.md" "$ROOT/docs/INSTALLATION_AND_BOOT.md" "$ROOT/docs/ISA_CATALOG.md"; do
  [[ -f "$f" ]] && cp "$f" "$DIST/chimera/docs/"
done
cp "$ROOT/boot/iso/iso-layout.json" "$DIST/ISO/"
printf '%s\n' 'Chimera II OS structured source-first ISO' > "$DIST/chimera/README.txt"
printf '%s\n' 'Boot: Spit Fire / Jasper; GRUB2 menu; kernel handoff: Koronos; media: ISO 9660 + El Torito.' >> "$DIST/chimera/README.txt"
printf '%s\n' 'ISA catalog: /src/ISA.csv; foreign drivers/binaries are metadata-only unless licensing, provenance and compatibility checks permit staging.' >> "$DIST/chimera/README.txt"
printf '%s\n' 'Support: created by Amer Abdullah Suleiman Hwitat | عامر الحويطات | Amman 11814/Jordan | amer.hwitat@proton.me' >> "$DIST/chimera/README.txt"
python3 "$ROOT/tools/isa/validate-isa.py"
python3 "$ROOT/boot/iso/validate-iso.py" --tree "$DIST" --write-manifest "$DIST/checksums/SHA256SUMS"
