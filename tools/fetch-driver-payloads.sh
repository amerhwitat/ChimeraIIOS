#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_DRIVER_BUILD_DIR:-$ROOT/build/drivers}"
mkdir -p "$OUT/modules" "$OUT/firmware" "$OUT/packages" "$OUT/manifests"
cp "$ROOT/drivers/driver-manifest.json" "$OUT/manifests/"

# Collect redistributable driver/firmware payloads from signed distro repositories.
# The native Koronos module ABI is separate from Linux .ko ABI; .ko files are
# staged for the compatibility layer and are never loaded directly by Koronos.
if command -v apt-get >/dev/null 2>&1; then
  for p in linux-firmware firmware-iwlwifi firmware-amd-graphics firmware-atheros firmware-brcm80211; do
    (cd "$OUT/packages" && apt-get download "$p" >/dev/null 2>&1) || echo "SKIP apt package: $p"
  done
fi

# Optional upstream linux-firmware snapshot. It is large, so this is explicit.
if [[ "${CHIMERA_FETCH_LINUX_FIRMWARE:-0}" == "1" ]]; then
  version="${CHIMERA_LINUX_FIRMWARE_VERSION:-20260916}"
  url="https://www.kernel.org/pub/linux/kernel/firmware/linux-firmware-$version.tar.xz"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 "$url" -o "$OUT/firmware/linux-firmware-$version.tar.xz"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$OUT/firmware/linux-firmware-$version.tar.xz" "$url"
  else
    echo "curl or wget required for linux-firmware download" >&2
    exit 2
  fi
fi

find "$OUT" -type f -print0 | sort -z | xargs -0r sha256sum > "$OUT/manifests/SHA256SUMS"
cat > "$OUT/manifests/driver-build.json" <<EOF
{"schema":"CHM-DRIVER-BUILD-1","koronos_native_modules":["virtio","generic-vga"],"compatibility_payloads":["linux-firmware","linux .ko packages"],"firmware_snapshot":"${CHIMERA_LINUX_FIRMWARE_VERSION:-20260916}","linux_firmware_downloaded":"${CHIMERA_FETCH_LINUX_FIRMWARE:-0}"}
EOF
printf 'Driver payload staging complete: %s\n' "$OUT"
