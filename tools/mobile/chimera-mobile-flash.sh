#!/usr/bin/env bash
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
    need python3
    exec python3 "$BUILDER" --detect
    ;;
  power-on|wake)
    need adb; need python3
    command -v fastboot >/dev/null 2>&1 || die "fastboot is required for safe bootloader-to-system wake."
    exec python3 "$BUILDER" --detect --power-on
    ;;
  rom-discover|discover-roms)
    need adb; need python3; [[ -f "$DISCOVERY" ]] || die "ROM discovery engine not found."
    exec python3 "$BUILDER" --discover-roms
    ;;
  build)
    need adb; need python3
    exec python3 "$BUILDER" --build
    ;;
  flash)
    need adb; need fastboot; need python3
    python3 "$BUILDER" --build
    REPORT="$ROOT/build/mobile/last-build.json"
    [[ -s "$REPORT" ]] || die "mobile build report was not generated"
    python3 - "$REPORT" <<'PY'
import hashlib,json,os,subprocess,sys
from pathlib import Path
r=json.load(open(sys.argv[1],encoding="utf-8"))
target=r.get("target",{}); serial=target.get("serial")
if not serial: raise SystemExit("No exact Android serial in build report.")
# Re-enumerate immediately before any write; this prevents flashing a replacement device.
q=subprocess.run(["adb","devices"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
live=[x.split()[0] for x in q.stdout.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=="device"]
if live != [serial]: raise SystemExit(f"Live device set changed; expected only {serial}, found {live}. Refusing to flash.")
p=r.get("profile",{}); flash=p.get("flash",{})
if flash.get("method")!="fastboot-profiled": raise SystemExit("No verified flash adapter exists for this exact device profile.")
parts=flash.get("partitions",[])
if not parts: raise SystemExit("Exact device profile declares no flash partitions; refusing to write.")
print("Verified exact device:",serial,p.get("id"),"architecture=",target.get("architecture"))
print("Partitions:",", ".join(x["name"] for x in parts))
answer=input('Type FLASH CHIMERA to continue: ')
if answer!="FLASH CHIMERA": raise SystemExit("Cancelled.")
for item in parts:
    image=Path(item["image"])
    if not image.is_file(): raise SystemExit("Missing mapped image: "+str(image))
    got=hashlib.sha256(image.read_bytes()).hexdigest()
    if got.lower()!=item["sha256"].lower(): raise SystemExit("SHA-256 mismatch: "+str(image))
    subprocess.run(["fastboot","-s",serial,"flash",item["name"],str(image)],check=True)
print("CHIMERA FLASH COMPLETE")
PY
    ;;
  --dry-run)
    need python3
    python3 "$BUILDER" --build
    echo "[DRY-RUN] Device-specific build and artifact verification completed; no phone partitions were written."
    ;;
  -h|--help|help)
    cat <<'EOF'
Chimera II OS Mobile Edition Flash Tool
  (no argument)       Aurora GUI
  ports               Scan USB, udev/sysfs, ADB, Fastboot, Apple usbmux, MTP, serial and Thunderbolt/USB4
  detect              Full host scan + Android hardware/software inspection
  inspect             Alias for detect
  power-on            Reboot a detected Fastboot phone into Android, then inspect it
  rom-discover        Discover exact-device public ROM/firmware/security metadata
  build               Build only for an exact matched Chimera device profile
  flash               Re-check exact serial/profile/hashes, then flash declared partitions
  --dry-run            Build/verify without writing a phone
Native Windows hosts can also run tools/mobile/chimera-device-port-scan.ps1.
EOF
    ;;
  *) die "unknown command: $COMMAND";;
esac
