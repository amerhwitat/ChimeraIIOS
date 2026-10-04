#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/mobile/chimera-mobile-build-upload.sh

Usage:
  tools/mobile/chimera-mobile-build-upload.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

# Chimera Mobile target orchestrator.
# Detects an attached phone, inventories hardware exposed by the vendor,
# builds the Chimera Mobile artifacts, validates the target architecture,
# and uploads artifacts sequentially to an authorized user-accessible staging
# directory. It deliberately does NOT bypass OEM authorization, FRP,
# Activation Lock, MDM, carrier locks, Secure Boot, or Verified Boot.

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${OUT:-$ROOT/build/mobile}
PROBE=${PROBE:-$ROOT/tools/mobile/chimera-mobile-probe.sh}
CATALOG=${CATALOG:-$ROOT/tools/mobile/mobile-os-catalog.json}
STAGE=${STAGE:-/sdcard/ChimeraMobile}
DRY_RUN=0
SKIP_BUILD=0
DISCOVER=0

usage(){
  cat <<'EOF'
Usage: chimera-mobile-build-upload.sh [options]
  --dry-run       detect/build/validate but never write to the phone
  --skip-build    use existing artifacts under build/mobile/artifacts
  --discover      refresh the public ROM/OS source manifest when curl is available
  --stage PATH    remote user-accessible staging path (default /sdcard/ChimeraMobile)
EOF
}
while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift;;
    --skip-build) SKIP_BUILD=1; shift;;
    --discover) DISCOVER=1; shift;;
    --stage) [[ $# -ge 2 ]] || { echo '[ERROR] --stage requires a path'; exit 2; }; STAGE=$2; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "[ERROR] Unknown option: $1"; usage; exit 2;;
  esac
done

mkdir -p "$OUT" "$OUT/artifacts"
command -v adb >/dev/null 2>&1 || { echo '[ERROR] adb is required'; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo '[ERROR] python3 is required'; exit 2; }

if (( DISCOVER )); then
  python3 "$ROOT/tools/mobile/discover-mobile-os.py" "$CATALOG" > "$OUT/rom-discovery.json"
  echo "[INFO] ROM/OS discovery manifest: $OUT/rom-discovery.json"
fi

printf '[1/6] Probing connected target...\n'
"$PROBE" | tee "$OUT/device-report.json"

python3 - "$OUT/device-report.json" "$OUT/target.json" <<'PY'
import json, sys
src, dst = sys.argv[1:]
data=json.load(open(src, encoding='utf-8'))
dev=[d for d in data.get('devices',[]) if d.get('transport') in ('adb','fastboot')]
if len(dev) != 1:
    raise SystemExit(f"expected exactly one connected mobile target, found {len(dev)}")
dev=dev[0]
abi=dev.get('architecture','')
if 'arm64' in abi.lower() or 'aarch64' in abi.lower(): arch='arm64'
elif 'armeabi' in abi.lower() or 'armv7' in abi.lower(): arch='arm32'
elif 'x86_64' in abi.lower(): arch='x86_64'
elif 'x86' in abi.lower(): arch='x86'
else: arch='unknown'
dev['normalized_arch']=arch
dev['chimera_flash_policy']='authorized-staging-only'
json.dump(dev, open(dst,'w',encoding='utf-8'), indent=2)
print(f"target={dev.get('manufacturer','')} {dev.get('model','')} transport={dev.get('transport')} arch={arch} unlock={dev.get('unlock_state')}")
PY

SERIAL=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$OUT/target.json")
TRANSPORT=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["transport"])' "$OUT/target.json")
ARCH=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["normalized_arch"])' "$OUT/target.json")

if [[ "$TRANSPORT" != adb ]]; then
  echo '[ERROR] Target is in bootloader/fastboot mode. Return to Android and authorize ADB for non-destructive staging.'
  exit 4
fi

printf '[2/6] Target architecture: %s\n' "$ARCH"
case "$ARCH" in arm64|arm32|x86|x86_64) ;; *) echo '[ERROR] Unsupported/unknown target ABI'; exit 5;; esac

if (( ! SKIP_BUILD )); then
  printf '[3/6] Building Chimera Mobile...\n'
  cmake -S "$ROOT" -B "$OUT/build" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_MOBILE=ON -DCHIMERA_TARGET_ARCH="$ARCH"
  cmake --build "$OUT/build" --parallel "$(nproc 2>/dev/null || echo 2)"
else
  printf '[3/6] Using existing mobile build.\n'
fi

printf '[4/6] Collecting and validating artifacts...\n'
find "$OUT/build" -type f \( -name '*.img' -o -name '*.bin' -o -name '*.zip' -o -name '*.dtb' -o -name '*.elf' \) -print 2>/dev/null | sort > "$OUT/artifacts.list" || true
if [[ ! -s "$OUT/artifacts.list" ]]; then
  find "$OUT/artifacts" -type f \( -name '*.img' -o -name '*.bin' -o -name '*.zip' -o -name '*.dtb' -o -name '*.elf' \) -print | sort > "$OUT/artifacts.list" || true
fi
[[ -s "$OUT/artifacts.list" ]] || { echo '[ERROR] No Chimera Mobile artifacts were produced.'; exit 6; }

python3 - "$OUT/artifacts.list" "$ARCH" "$OUT/artifact-manifest.json" <<'PY'
import hashlib,json,os,sys
lst,arch,out=sys.argv[1:]
items=[]
for line in open(lst,encoding='utf-8'):
    p=line.strip()
    if not p: continue
    with open(p,'rb') as f: data=f.read()
    items.append({'path':os.path.abspath(p),'name':os.path.basename(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'target_arch':arch})
json.dump({'schema':1,'target_arch':arch,'artifacts':items},open(out,'w',encoding='utf-8'),indent=2)
print(f'{len(items)} artifact(s) validated')
PY

printf '[5/6] Artifact manifest:\n'
cat "$OUT/artifact-manifest.json"

if (( DRY_RUN )); then
  echo '[DRY-RUN] No phone writes performed.'
  exit 0
fi

read -r -p 'Type FLASH CHIMERA to upload artifacts sequentially to user-accessible staging: ' answer
[[ "$answer" == 'FLASH CHIMERA' ]] || { echo '[INFO] Write operation cancelled.'; exit 0; }

printf '[6/6] Sequential upload to %s...\n' "$STAGE"
adb -s "$SERIAL" shell "mkdir -p '$STAGE'"
while IFS= read -r artifact; do
  [[ -f "$artifact" ]] || continue
  base=$(basename "$artifact")
  echo "[UPLOAD] $base"
  adb -s "$SERIAL" push "$artifact" "$STAGE/$base"
done < "$OUT/artifacts.list"

echo '[SUCCESS] All Chimera Mobile artifacts were uploaded sequentially.'
echo '[INFO] No Android partition was overwritten by this generic orchestrator.'
echo '[INFO] Device-specific flashing remains gated behind a verified vendor/device adapter.'
