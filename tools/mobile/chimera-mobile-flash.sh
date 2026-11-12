#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/mobile/chimera-mobile-flash.sh

Usage:
  tools/mobile/chimera-mobile-flash.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
GUI="$SCRIPT_DIR/chimera-mobile-flash-gui.py"
BUILDER="$SCRIPT_DIR/chimera-mobile-build.py"
DISCOVERY="$SCRIPT_DIR/chimera-mobile-rom-discovery.py"
SCANNER="$SCRIPT_DIR/chimera-device-port-scan.py"
die(){ echo "[ERROR] $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"; }
COMMAND="${1:-gui}"

generic_flash() {
  die "generic-flash is disabled. Phone writes require a hardware-validated exact-device profile, vendor-approved adapter, signed images, verified hashes, and explicit device confirmation."
}

case "$COMMAND" in
  gui|--gui)
    need python3; [[ -f "$GUI" ]] || die "GUI not found: $GUI"
    [[ -f "$BUILDER" ]] || die "mobile builder not found: $BUILDER"
    python3 -c 'import tkinter' >/dev/null 2>&1 || die "Python Tkinter is not installed."
    [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]] || die "No graphical display detected."
    exec python3 "$GUI"
    ;;
  ports|port-scan|usb|usb-scan)
    need python3; [[ -f "$SCANNER" ]] || die "universal port scanner not found: $SCANNER"
    exec python3 "$SCANNER" --json
    ;;
  detect|inspect)
    need python3; exec python3 "$BUILDER" --detect ;;
  power-on|wake)
    need adb; need python3; command -v fastboot >/dev/null 2>&1 || die "fastboot required."
    exec python3 "$BUILDER" --detect --power-on
    ;;
  rom-discover|discover-roms)
    need adb; need python3; [[ -f "$DISCOVERY" ]] || die "ROM discovery engine not found."
    exec python3 "$BUILDER" --discover-roms
    ;;
  build)
    need adb; need python3; exec python3 "$BUILDER" --build ;;
  flash)
    need adb; need fastboot; need python3
    python3 "$BUILDER" --build
    REPORT="$ROOT/build/mobile/last-build.json"
    [[ -s "$REPORT" ]] || die "mobile build report was not generated"
    python3 "$SCRIPT_DIR/chimera-mobile-fastboot.py" "$REPORT"
    ;;
  generic-flash)
    generic_flash
    ;;
  --dry-run)
    need python3; python3 "$BUILDER" --build
    echo "[DRY-RUN] Device-specific build and artifact verification completed; no phone partitions were written."
    ;;
  -h|--help|help)
    cat <<'EOF'
Chimera II OS Mobile Edition Flash Tool
  (no argument)       Aurora GUI
  ports               Scan USB, udev/sysfs, ADB, Fastboot, Apple usbmux, MTP, serial and Thunderbolt/USB4
  detect              Inspect connected Android device and host capabilities
  power-on            Request a supported reboot to Fastboot
  rom-discover        Discover public ROM/firmware metadata
  build               Build only for an exact matched device profile
  flash               Profiled flashing with device, signature and hash checks
  generic-flash       Disabled; unprofiled partition writes are refused
  --dry-run           Build and verify without writing a phone

A flashable image requires an exact hardware-validated device profile, signed
vendor boot components, a supported device-specific adapter, matching serial
and product identity, verified image hashes, and explicit confirmation.
Generic profiles are reference-only and cannot authorize partition writes.
EOF
    ;;
  *) die "unknown command: $COMMAND";;
esac
