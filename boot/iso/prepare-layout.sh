#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST="$ROOT/boot/iso/dist/iso"
rm -rf "$DIST"
mkdir -p "$DIST/boot/grub" "$DIST/boot/jasper" "$DIST/boot/spitfire" "$DIST/boot/koronos" "$DIST/EFI/BOOT" "$DIST/EFI/CHIMERA"
mkdir -p "$DIST/chimera/manifests" "$DIST/chimera/docs" "$DIST/usr/share/chimera/aurora" "$DIST/install" "$DIST/checksums"

# Canonical kernel payload: the exact ELF validated by grub-file and loaded by GRUB's multiboot2 command.
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
[[ -s "$KERNEL" ]] || { echo "Koronos kernel ELF missing: $KERNEL" >&2; exit 1; }
cp "$KERNEL" "$DIST/boot/kernel.bin"
cp "$KERNEL" "$DIST/boot/koronos/koronos.elf"

# Bootloader source/artifacts and Jasper recovery configuration.
cp "$ROOT/boot/spitfire/sf0_mbr.asm" "$ROOT/boot/spitfire/sf1_longmode.asm" "$ROOT/boot/spitfire/sf2_loader.cpp" "$ROOT/boot/spitfire/sf2_loader.h" "$ROOT/boot/spitfire/spitfire.ld" "$DIST/boot/spitfire/"
cp "$ROOT/boot/spitfire/sfu_uefi.c" "$ROOT/boot/spitfire/sfu_uefi.h" "$ROOT/boot/spitfire/sfu_uefi.ld" "$DIST/EFI/CHIMERA/"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/grub/grub.cfg"
cp "$ROOT/boot/iso/grub.cfg" "$DIST/boot/jasper/grub.cfg"
cat > "$DIST/boot/jasper/recovery.cfg" <<'EOF'
set timeout=5
set default=0
insmod normal
insmod gfxterm
insmod png
insmod search
if [ -f /boot/jasper/background.png ]; then background_image /boot/jasper/background.png; fi
menuentry "Jasper Recovery — Koronos Rescue" { multiboot2 /boot/kernel.bin chm.mode=recovery chm.recovery=1; boot }
menuentry "Jasper Recovery — Safe Graphics" { multiboot2 /boot/kernel.bin chm.mode=safe-graphics; boot }
menuentry "Jasper Recovery — GRUB Command Line" { commandline }
menuentry "Jasper Recovery — Reboot" { reboot }
menuentry "Jasper Recovery — Power Off" { halt }
EOF

[[ -f "$ROOT/boot/boot_protocol.json" ]] && cp "$ROOT/boot/boot_protocol.json" "$DIST/boot/"
[[ -f "$ROOT/boot/startup/boot_phase_manifest.json" ]] && cp "$ROOT/boot/startup/boot_phase_manifest.json" "$DIST/boot/"

# Aurora source artwork is kept in the ISO; raster PNGs are generated for GRUB and installer windows.
RASTERIZER=""
if command -v rsvg-convert >/dev/null 2>&1; then RASTERIZER=rsvg-convert
elif command -v convert >/dev/null 2>&1; then RASTERIZER=convert
else echo "Aurora artwork requires rsvg-convert or ImageMagick." >&2; exit 2
fi

if [[ "$RASTERIZER" == "rsvg-convert" ]]; then
  rsvg-convert -w 1920 -h 1080 "$ROOT/desktop/aurora/assets/aurora-wayland-glass.svg" -o "$DIST/boot/grub/aurora-wayland-glass.png"
  rsvg-convert -w 1920 -h 1080 "$ROOT/desktop/aurora/assets/aurora-installer.svg" -o "$DIST/install/installer-background.png"
  rsvg-convert -w 1920 -h 1080 "$ROOT/desktop/aurora/assets/aurora-library.svg" -o "$DIST/usr/share/chimera/aurora/library-background.png"
  rsvg-convert -w 1920 -h 1080 "$ROOT/desktop/aurora/assets/aurora-desktop.svg" -o "$DIST/usr/share/chimera/aurora/desktop-background.png"
  rsvg-convert -w 1920 -h 1080 "$ROOT/boot/splash/jasper_background.svg" -o "$DIST/boot/jasper/background.png"
  rsvg-convert -w 1920 -h 1080 "$ROOT/boot/splash/spitfire_background.svg" -o "$DIST/boot/spitfire/background.png"
else
  convert -background none "$ROOT/desktop/aurora/assets/aurora-wayland-glass.svg" "$DIST/boot/grub/aurora-wayland-glass.png"
  convert -background none "$ROOT/desktop/aurora/assets/aurora-installer.svg" "$DIST/install/installer-background.png"
  convert -background none "$ROOT/desktop/aurora/assets/aurora-library.svg" "$DIST/usr/share/chimera/aurora/library-background.png"
  convert -background none "$ROOT/desktop/aurora/assets/aurora-desktop.svg" "$DIST/usr/share/chimera/aurora/desktop-background.png"
  convert -background none "$ROOT/boot/splash/jasper_background.svg" "$DIST/boot/jasper/background.png"
  convert -background none "$ROOT/boot/splash/spitfire_background.svg" "$DIST/boot/spitfire/background.png"
fi
cp "$ROOT/desktop/aurora/assets/aurora-wayland-glass.svg" "$ROOT/desktop/aurora/assets/aurora-installer.svg" "$ROOT/desktop/aurora/assets/aurora-library.svg" "$ROOT/desktop/aurora/assets/aurora-desktop.svg" "$DIST/usr/share/chimera/aurora/"

# Installer/desktop background manifest gives every installer window a deterministic visual asset.
cat > "$DIST/install/background-manifest.json" <<'EOF'
{
  "schema": "CHM-INSTALL-BACKGROUNDS-1",
  "default": "/install/installer-background.png",
  "steps": {
    "welcome": "/install/installer-background.png",
    "hardware": "/usr/share/chimera/aurora/library-background.png",
    "mode": "/usr/share/chimera/aurora/desktop-background.png",
    "target": "/usr/share/chimera/aurora/desktop-background.png",
    "storage": "/usr/share/chimera/aurora/desktop-background.png",
    "boot": "/boot/spitfire/background.png",
    "software": "/usr/share/chimera/aurora/library-background.png",
    "security": "/boot/jasper/background.png",
    "tools": "/usr/share/chimera/aurora/library-background.png",
    "users": "/usr/share/chimera/aurora/desktop-background.png",
    "install": "/install/installer-background.png",
    "validate": "/boot/jasper/background.png",
    "reboot": "/boot/grub/aurora-wayland-glass.png"
  }
}
EOF

[[ -f "$ROOT/installer/installation_phases.json" ]] && cp "$ROOT/installer/installation_phases.json" "$DIST/chimera/manifests/"
[[ -f "$ROOT/installer/installer_profiles.json" ]] && cp "$ROOT/installer/installer_profiles.json" "$DIST/chimera/manifests/"
[[ -f "$ROOT/installer/chimera-installer-plan.json" ]] && cp "$ROOT/installer/chimera-installer-plan.json" "$DIST/chimera/manifests/"
[[ -f "$ROOT/README.md" ]] && cp "$ROOT/README.md" "$DIST/chimera/docs/"

python3 "$ROOT/boot/iso/validate-iso.py" --tree "$DIST" --write-manifest "$DIST/checksums/SHA256SUMS"
