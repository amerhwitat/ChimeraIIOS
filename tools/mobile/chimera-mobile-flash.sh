#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "\${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
GUI="$SCRIPT_DIR/chimera-mobile-flash-gui.py"
BUILDER="$SCRIPT_DIR/chimera-mobile-build.py"
die(){ echo "[ERROR] $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"; }
case "\${1:-gui}" in
  gui|--gui) need python3; [[ -f "$GUI" ]] || die "GUI not found: $GUI"; exec python3 "$GUI" ;;
  detect) need adb; need python3; exec python3 "$BUILDER" --detect ;;
  build) need adb; need python3; exec python3 "$BUILDER" --build ;;
  flash)
    need adb; need fastboot; need python3
    python3 "$BUILDER" --build
    REPORT="$ROOT/build/mobile/last-build.json"
    [[ -s "$REPORT" ]] || die "mobile build report was not generated"
    read -r -p 'Type FLASH CHIMERA to continue: ' ANSWER
    [[ "$ANSWER" == "FLASH CHIMERA" ]] || { echo "Cancelled."; exit 0; }
    python3 - "$REPORT" <<'PY'
import hashlib,json,os,subprocess,sys
r=json.load(open(sys.argv[1],encoding="utf-8")); f=r["profile"].get("flash",{})
if f.get("method")!="fastboot-profiled": raise SystemExit("No verified flash adapter exists for this exact device profile.")
for x in f.get("partitions",[]):
    p=x["image"]
    if not os.path.isfile(p): raise SystemExit("Missing mapped image: "+p)
    with open(p,"rb") as h: got=hashlib.sha256(h.read()).hexdigest()
    if got.lower()!=x["sha256"].lower(): raise SystemExit("SHA-256 mismatch: "+p)
    subprocess.run(["fastboot","-s",r["target"]["serial"],"flash",x["name"],p],check=True)
print("CHIMERA FLASH COMPLETE")
PY
    ;;
  --dry-run) need adb; need python3; python3 "$BUILDER" --build; echo "[DRY-RUN] No phone partitions were written." ;;
  -h|--help|help) echo "chimera-mobile-flash.sh [--gui|detect|build|--dry-run|flash]" ;;
  *) die "unknown command: $1" ;;
esac
