#!/usr/bin/env bash
set -euo pipefail

# Build Chimera Mobile artifacts and, only after explicit confirmation,
# upload them sequentially to an authorized Android target.
# This script deliberately does not bypass bootloader, FRP, Activation Lock,
# MDM, carrier locks, secure boot, or OEM authorization.

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${OUT:-$ROOT/build/mobile}
PROBE=${PROBE:-$ROOT/tools/mobile/chimera-mobile-probe.sh}
mkdir -p "$OUT"

command -v adb >/dev/null 2>&1 || { echo '[ERROR] adb is required'; exit 2; }
command -v cmake >/dev/null 2>&1 || { echo '[ERROR] cmake is required'; exit 2; }

printf '[1/5] Probing target...\n'
"$PROBE" | tee "$OUT/device-report.json"

mapfile -t DEVICES < <(adb devices | awk 'NR>1 && $2=="device" {print $1}')
if (( ${#DEVICES[@]} != 1 )); then
  echo '[ERROR] Exactly one authorized ADB device must be connected.'
  exit 3
fi
SERIAL=${DEVICES[0]}

arch=$(adb -s "$SERIAL" shell getprop ro.product.cpu.abi 2>/dev/null | tr -d '\r')
model=$(adb -s "$SERIAL" shell getprop ro.product.model 2>/dev/null | tr -d '\r')
locked=$(adb -s "$SERIAL" shell getprop ro.boot.flash.locked 2>/dev/null | tr -d '\r')

printf '[2/5] Target: %s (%s), ABI=%s, flash.locked=%s\n' "$model" "$SERIAL" "$arch" "$locked"
[[ "$locked" == "0" ]] || { echo '[ERROR] Bootloader is not reported unlocked; use the OEM-supported unlock procedure first.'; exit 4; }

printf '[3/5] Building Chimera Mobile...\n'
cmake -S "$ROOT" -B "$OUT/build" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_MOBILE=ON
cmake --build "$OUT/build" --parallel "$(nproc 2>/dev/null || echo 2)"

printf '[4/5] Staging artifacts...\n'
find "$OUT/build" -type f \( -name '*.img' -o -name '*.bin' -o -name '*.zip' -o -name '*.dtb' \) -print > "$OUT/artifacts.list"
[[ -s "$OUT/artifacts.list" ]] || { echo '[ERROR] No mobile artifacts were produced.'; exit 5; }

printf '[5/5] Ready for sequential upload.\n'
echo 'The following artifacts will be uploaded one at a time:'
cat "$OUT/artifacts.list"
echo
read -r -p 'Type FLASH CHIMERA to continue: ' answer
[[ "$answer" == 'FLASH CHIMERA' ]] || { echo '[INFO] Write operation cancelled.'; exit 0; }

while IFS= read -r artifact; do
  base=$(basename "$artifact")
  echo "[UPLOAD] $base"
  # Upload to user-accessible staging only. Actual partition flashing is
  # delegated to a device-specific adapter after partition mapping and
  # signature/compatibility checks.
  adb -s "$SERIAL" push "$artifact" "/sdcard/ChimeraMobile/$base"
done < "$OUT/artifacts.list"

echo '[SUCCESS] Chimera Mobile artifacts uploaded sequentially.'
echo '[INFO] No partition was overwritten by this generic uploader.'
echo '[INFO] Device-specific flashing requires a verified adapter and explicit partition map.'
