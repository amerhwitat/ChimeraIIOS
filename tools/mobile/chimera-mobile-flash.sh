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

generic_flash() {
  need fastboot
  local serial="${GENERIC_SERIAL:-}" manifest="${GENERIC_MANIFEST:-}"
  [[ -n "$serial" ]] || die "Set GENERIC_SERIAL to the exact Fastboot serial."
  [[ -n "$manifest" && -f "$manifest" ]] || die "Set GENERIC_MANIFEST to a JSON partition manifest."
  python3 - "$serial" "$manifest" <<'PY'
import hashlib,json,os,subprocess,sys
from pathlib import Path
serial,manifest=sys.argv[1],Path(sys.argv[2])
try: m=json.loads(manifest.read_text(encoding="utf-8"))
except Exception as e: raise SystemExit("Invalid generic flash manifest: "+str(e))
if m.get("schema")!="CHM-GENERIC-FLASH-1":
    raise SystemExit("Manifest schema must be CHM-GENERIC-FLASH-1")
parts=m.get("partitions",[])
if not parts: raise SystemExit("Manifest contains no partitions.")
if len(parts)>64: raise SystemExit("Refusing more than 64 partition writes in one generic operation.")
q=subprocess.run(["fastboot","devices"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
live=[x.split()[0] for x in q.stdout.splitlines() if x.split()]
if live != [serial]:
    raise SystemExit(f"Live Fastboot device mismatch: expected only {serial}, found {live}")
print("\nWARNING: GENERIC PARTITION FLASH MODE")
print("This mode deliberately does NOT require a Chimera exact-device profile.")
print("It can erase/overwrite incompatible partitions and may permanently brick a device.")
print("The manifest must explicitly name every partition and image.")
print("Device:",serial)
for x in parts:
    name=x.get("name",""); image=Path(x.get("image",""))
    if not name or not image.is_file(): raise SystemExit("Invalid partition/image entry: "+str(x))
    if "/" in name or "\\" in name or name in {".",".."}: raise SystemExit("Unsafe partition name: "+name)
    if "sha256" not in x: raise SystemExit("Every generic image must have a SHA-256: "+name)
    got=hashlib.sha256(image.read_bytes()).hexdigest()
    if got.lower()!=str(x["sha256"]).lower(): raise SystemExit("SHA-256 mismatch: "+name)
    print(f"  {name} <- {image}  sha256={got}")
if m.get("backup_manifest"):
    Path(m["backup_manifest"]).write_text(json.dumps({"serial":serial,"partitions":[x["name"] for x in parts]},indent=2)+"\n")
if os.environ.get("CHIMERA_GENERIC_FLASH_ACK")!="I_UNDERSTAND_GENERIC_FLASH_IS_DANGEROUS":
    raise SystemExit("Set CHIMERA_GENERIC_FLASH_ACK=I_UNDERSTAND_GENERIC_FLASH_IS_DANGEROUS to enable generic writes.")
answer=input('Type GENERIC FLASH CHIMERA to continue: ')
if answer!="GENERIC FLASH CHIMERA": raise SystemExit("Cancelled.")
for x in parts:
    subprocess.run(["fastboot","-s",serial,"flash",x["name"],x["image"]],check=True)
print("GENERIC CHIMERA FLASH COMPLETE")
PY
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
    python3 - "$REPORT" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
r=json.load(open(sys.argv[1],encoding="utf-8")); target=r.get("target",{}); serial=target.get("serial")
if not serial: raise SystemExit("No exact Android serial in build report.")
q=subprocess.run(["adb","devices"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
live=[x.split()[0] for x in q.stdout.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=="device"]
if live != [serial]: raise SystemExit(f"Live device set changed; expected only {serial}, found {live}. Refusing to flash.")
p=r.get("profile",{}); flash=p.get("flash",{})
if flash.get("method")!="fastboot-profiled": raise SystemExit("No verified flash adapter exists for this exact device profile.")
parts=flash.get("partitions",[])
if not parts: raise SystemExit("Exact device profile declares no flash partitions; refusing to write.")
print("Verified exact device:",serial,p.get("id"),"architecture=",target.get("architecture"))
print("Partitions:",", ".join(x["name"] for x in parts))
if input('Type FLASH CHIMERA to continue: ')!="FLASH CHIMERA": raise SystemExit("Cancelled.")
for item in parts:
    image=Path(item["image"])
    if not image.is_file(): raise SystemExit("Missing mapped image: "+str(image))
    if hashlib.sha256(image.read_bytes()).hexdigest().lower()!=item["sha256"].lower(): raise SystemExit("SHA-256 mismatch: "+str(image))
    subprocess.run(["fastboot","-s",serial,"flash",item["name"],str(image)],check=True)
print("CHIMERA FLASH COMPLETE")
PY
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
  detect              Full host scan + Android hardware/software inspection
  inspect             Alias for detect
  power-on            Reboot a detected Fastboot phone into Android, then inspect it
  rom-discover        Discover exact-device public ROM/firmware/security metadata
  build               Build only for an exact matched Chimera device profile
  flash               Profiled, exact-device flashing with hash verification
  generic-flash       Advanced generic Fastboot partition flashing from an explicit manifest
  --dry-run            Build/verify without writing a phone

GENERIC FLASH SAFETY CONTRACT:
  GENERIC_SERIAL=<exact-fastboot-serial>
  GENERIC_MANIFEST=/path/to/manifest.json
  CHIMERA_GENERIC_FLASH_ACK=I_UNDERSTAND_GENERIC_FLASH_IS_DANGEROUS

Manifest schema:
  {"schema":"CHM-GENERIC-FLASH-1",
   "partitions":[{"name":"boot","image":"/path/boot.img","sha256":"..."}]}
EOF
    ;;
  *) die "unknown command: $COMMAND";;
esac
