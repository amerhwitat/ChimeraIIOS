#!/usr/bin/env bash
set -Eeuo pipefail

# Chimera Mobile Flash: owner-authorized recovery/flashing helper.
# This tool intentionally does NOT bypass FRP, iCloud/Activation Lock, MDM,
# carrier restrictions, OEM authorization, or vendor security controls.

usage() {
  cat <<'EOF'
Usage:
  chimera-mobile-flash.sh detect
  chimera-mobile-flash.sh backup-info
  chimera-mobile-flash.sh android-info
  chimera-mobile-flash.sh android-unlock
  chimera-mobile-flash.sh android-flash IMAGE [PARTITION]
  chimera-mobile-flash.sh android-reboot MODE
  chimera-mobile-flash.sh ios-info
  chimera-mobile-flash.sh ios-recovery

Android unlock requires the device's normal OEM-supported unlock path and
explicit confirmation on the device. Flashing requires an image supplied by
the owner and an explicitly specified partition.
EOF
}

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing dependency: $1" >&2; exit 127; }; }

android_unlock() {
  need adb; need fastboot
  echo "Checking Android device authorization state..."
  adb get-state >/dev/null 2>&1 || true
  echo "Rebooting to bootloader; complete OEM unlocking on the device if supported."
  adb reboot bootloader
  echo "Device must explicitly confirm the OEM unlock operation."
  echo "No FRP, Google-account, enterprise, carrier, or other lock bypass is attempted."
}

android_flash() {
  need fastboot
  local image="$1" partition="${2:-}"
  [[ -f "$image" ]] || { echo "ERROR: image not found: $image" >&2; exit 2; }
  [[ -n "$partition" ]] || { echo "ERROR: partition is required; refusing ambiguous flashing." >&2; exit 2; }
  echo "fastboot device:"; fastboot devices
  echo "Flashing $image to explicitly requested partition '$partition'."
  fastboot flash "$partition" "$image"
}

case "${1:-}" in
  detect) command -v adb >/dev/null 2>&1 && adb devices -l || true; command -v fastboot >/dev/null 2>&1 && fastboot devices || true;;
  backup-info) echo "Backup before unlocking/flashing. Android OEM unlock normally wipes user data.";;
  android-info) need adb; adb shell getprop ro.product.manufacturer; adb shell getprop ro.product.model; adb shell getprop ro.boot.verifiedbootstate;;
  android-unlock) android_unlock;;
  android-flash) shift; android_flash "$@";;
  android-reboot) need adb; adb reboot "${2:-bootloader}";;
  ios-info) need idevice_id; idevice_id -l || true; command -v ideviceinfo >/dev/null 2>&1 && ideviceinfo -s || true;;
  ios-recovery) echo "Use Apple's supported recovery/restore workflow. No Activation Lock bypass is attempted.";;
  *) usage; exit 2;;
esac
