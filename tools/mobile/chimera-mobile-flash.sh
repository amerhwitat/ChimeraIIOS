#!/usr/bin/env bash
set -Eeuo pipefail
D="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"; ROOT="$(cd "$D/../.." && pwd)"
GUI="$D/chimera-mobile-flash-gui.py"; BUILDER="$D/chimera-mobile-build.py"
need(){ command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] missing dependency: $1"; exit 127; }; }
case "\${1:-gui}" in
 gui|--gui) need python3; exec python3 "$GUI";;
 detect) need adb; need python3; python3 "$BUILDER" --detect;;
 build) need adb; need python3; python3 "$BUILDER" --build;;
 flash) need adb; need fastboot; need python3; python3 "$BUILDER" --build; read -r -p 'Type FLASH CHIMERA to continue: ' A; [[ "$A" == "FLASH CHIMERA" ]] || exit 0
  python3 - "$ROOT/build/mobile/last-build.json" <<'PY'
import json,subprocess,sys,hashlib,os
r=json.load(open(sys.argv[1])); p=r["profile"]; t=r["target"]; f=p.get("flash",{})
if f.get("method")!="fastboot-profiled": raise SystemExit("No verified flash adapter for this exact profile.")
for x in f["partitions"]:
 path=x["image"]
 if not os.path.isfile(path): raise SystemExit("Missing mapped image: "+path)
 if hashlib.sha256(open(path,"rb").read()).hexdigest().lower()!=x["sha256"].lower(): raise SystemExit("SHA-256 mismatch: "+path)
 subprocess.run(["fastboot","-s",t["serial"],"flash",x["name"],path],check=True)
print("CHIMERA FLASH COMPLETE")
PY
 ;;
 --dry-run) need adb; need python3; python3 "$BUILDER" --build; echo "[DRY-RUN] no phone partitions written";;
 -h|--help|help) echo "chimera-mobile-flash.sh [detect|build|flash|--dry-run|--gui]";;
 *) echo "unknown command"; exit 2;;
esac
