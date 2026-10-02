#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
GUI="$SCRIPT_DIR/chimera-mobile-flash-gui.py"
BUILDER="$SCRIPT_DIR/chimera-mobile-build.py"

die(){ echo "[ERROR] $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"; }

# No argument means GUI. Never dereference $1 directly under set -u.
COMMAND="${1:-gui}"

case "$COMMAND" in
  gui|--gui)
    need python3
    [[ -f "$GUI" ]] || die "GUI not found: $GUI"
    [[ -f "$BUILDER" ]] || die "mobile builder not found: $BUILDER"
    if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
      die "Python Tkinter is not installed. Install python3-tk, then rerun this command."
    fi
    if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
      die "No graphical display detected. In WSL, enable WSLg or X/Wayland, or run: tools/mobile/chimera-mobile-flash.sh detect"
    fi
    exec python3 "$GUI"
    ;;

  detect)
    need adb
    need python3
    exec python3 "$BUILDER" --detect
    ;;

  build)
    need adb
    need python3
    exec python3 "$BUILDER" --build
    ;;

  flash)
    need adb
    need fastboot
    need python3
    python3 "$BUILDER" --build
    REPORT="$ROOT/build/mobile/last-build.json"
    [[ -s "$REPORT" ]] || die "mobile build report was not generated"
    read -r -p 'Type FLASH CHIMERA to continue: ' ANSWER
    [[ "$ANSWER" == "FLASH CHIMERA" ]] || { echo "Cancelled."; exit 0; }
    python3 - "$REPORT" <<'PY'
import hashlib
import json
import os
import subprocess
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    report = json.load(fh)

flash = report.get("profile", {}).get("flash", {})
if flash.get("method") != "fastboot-profiled":
    raise SystemExit("No verified flash adapter exists for this exact device profile.")

partitions = flash.get("partitions", [])
if not partitions:
    raise SystemExit("The exact device profile declares no flash partitions; refusing to write anything.")

for item in partitions:
    image = item["image"]
    if not os.path.isfile(image):
        raise SystemExit("Missing mapped image: " + image)
    with open(image, "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()
    if got.lower() != item["sha256"].lower():
        raise SystemExit("SHA-256 mismatch: " + image)
    subprocess.run(
        ["fastboot", "-s", report["target"]["serial"], "flash", item["name"], image],
        check=True,
    )

print("CHIMERA FLASH COMPLETE")
PY
    ;;

  --dry-run)
    need adb
    need python3
    python3 "$BUILDER" --build
    echo "[DRY-RUN] Build and artifact verification completed; no phone partitions were written."
    ;;

  -h|--help|help)
    cat <<'EOF'
Chimera II OS Mobile Edition Flash Tool

Usage:
  tools/mobile/chimera-mobile-flash.sh
  tools/mobile/chimera-mobile-flash.sh --gui
  tools/mobile/chimera-mobile-flash.sh detect
  tools/mobile/chimera-mobile-flash.sh build
  tools/mobile/chimera-mobile-flash.sh --dry-run
  tools/mobile/chimera-mobile-flash.sh flash

No argument defaults to the GUI.
EOF
    ;;

  *)
    die "unknown command: $COMMAND"
    ;;
esac
