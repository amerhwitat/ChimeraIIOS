#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/mobile"
ARCH="${CHIMERA_MOBILE_ARCH:-aarch64}"
PROFILE="${CHIMERA_MOBILE_PROFILE:-generic-aarch64}"
mkdir -p "$OUT" "$OUT/images" "$OUT/manifests"

command -v sha256sum >/dev/null 2>&1 || { echo "sha256sum is required" >&2; exit 2; }
test -f "$ROOT/build/koronos/x86_64/koronos.elf" || {
  echo "Koronos host build is missing; run kernel/build-koronos.sh first." >&2; exit 3;
}

# Mobile edition is deliberately split into a common, device-independent
# runtime payload and a device-specific boot/adaptation bundle. This prevents
# an x86_64 desktop kernel from being flashed onto an ARM phone.
cp -f "$ROOT/build/koronos/x86_64/koronos.elf" "$OUT/images/koronos-reference-host.elf"
cat > "$OUT/manifests/mobile-edition.json" <<EOF
{
  "schema": "CHM-MOBILE-EDITION-2",
  "architecture": "$ARCH",
  "profile": "$PROFILE",
  "runtime": {
    "shared": ["Koronos IPC/capability ABI", "N-bit execution policy", "security policy", "database/runtime services"],
    "requires_device_boot_bundle": true,
    "requires_device_driver_bundle": true
  },
  "deployment": {
    "android": ["adb", "fastboot", "recovery-sideload"],
    "apple": ["xcodebuild/archive", "device-specific signed deployment"]
  },
  "safety": {
    "generic_partition_flash": false,
    "exact_device_manifest_required": true,
    "image_hash_required": true,
    "signature_required": true,
    "rollback_metadata_required": true,
    "bootloader_unlock_must_be_explicit": true
  }
}
EOF
sha256sum "$OUT/manifests/mobile-edition.json" > "$OUT/manifests/SHA256SUMS"
printf 'Mobile edition manifest: %s\n' "$OUT/manifests/mobile-edition.json"
printf 'Architecture: %s; profile: %s\n' "$ARCH" "$PROFILE"
printf 'Device-specific boot images are intentionally not synthesized from the desktop ELF.\n'
