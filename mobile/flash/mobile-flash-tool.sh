#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="$ROOT/build/mobile"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
usage(){ echo "Usage: $0 --detect | --discover | --prepare | --flash --device CODENAME --rom IMAGE [--kernel FILE]"; }
require(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 2; }; }
detect(){ command -v adb >/dev/null 2>&1 && adb devices || true; command -v fastboot >/dev/null 2>&1 && fastboot devices || true; }
discover(){ require curl; mkdir -p "$OUT/resources"; curl -fsSL --retry 3 https://raw.githubusercontent.com/amerhwitat/ChimeraIIOS/main/config/mobile-os-sources.json -o "$OUT/resources/mobile-os-sources.json"; cat "$OUT/resources/mobile-os-sources.json"; }
prepare(){ mkdir -p "$OUT/payload"; test -f "$KERNEL" || { echo "Koronos kernel not found: $KERNEL" >&2; exit 3; }; cp -f "$KERNEL" "$OUT/payload/koronos-kernel.elf"; test -d "$ROOT/build/mobile/apps" && cp -a "$ROOT/build/mobile/apps" "$OUT/payload/apps" || true; sha256sum "$OUT/payload"/* > "$OUT/payload/SHA256SUMS" 2>/dev/null || true; echo '{"schema":"CHM-MOBILE-PAYLOAD-1","requires_device_specific_boot_image":true}' > "$OUT/payload/manifest.json"; }
flash(){ require fastboot; test -n "$DEVICE" && test -f "$ROM" || { echo "Exact device codename and ROM are required." >&2; exit 4; }; prepare; echo "Flashing can erase data or brick unsupported hardware."; read -r -p "Type FLASH $DEVICE to continue: " confirm; test "$confirm" = "FLASH $DEVICE" || { echo "Flash cancelled."; exit 6; }; echo "Payload prepared; no generic partition is flashed. A verified device manifest must define the exact boot/ROM procedure."; }
case "$1" in
--detect) detect;;
--discover) discover;;
--prepare) prepare;;
--flash) shift; DEVICE=""; ROM=""; while (($#)); do case "$1" in --device) DEVICE="$2"; shift 2;; --rom) ROM="$2"; shift 2;; --kernel) KERNEL="$2"; shift 2;; *) usage; exit 2;; esac; done; flash;;
*) usage; exit 2;;
esac
