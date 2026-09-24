#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_DRIVER_BUILD_DIR:-$ROOT/build/drivers}"
mkdir -p "$OUT/modules" "$OUT/firmware" "$OUT/packages" "$OUT/manifests" "$OUT/firmware/rootfs"
cp "$ROOT/drivers/driver-manifest.json" "$OUT/manifests/"

apt_has() { command -v apt-cache >/dev/null 2>&1 && apt-cache show "$1" >/dev/null 2>&1; }
download() { local p="$1"; (cd "$OUT/packages" && apt-get download "$p" >/dev/null 2>&1); }

if command -v apt-get >/dev/null 2>&1; then
  staged=0
  for p in linux-firmware firmware-iwlwifi firmware-amd-graphics firmware-atheros firmware-brcm80211; do
    if apt_has "$p" && download "$p"; then
      echo "STAGED apt package: $p"
      staged=1
    else
      echo "INFO apt package unavailable: $p"
    fi
  done
  if [[ "$staged" == "0" ]] && apt_has linux-firmware; then
    download linux-firmware && echo "STAGED consolidated firmware package: linux-firmware"
  fi
fi

for deb in "$OUT/packages/"*.deb; do
  [[ -f "$deb" ]] || continue
  dpkg-deb -x "$deb" "$OUT/firmware/rootfs" 2>/dev/null || true
done

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
{"schema":"CHM-DRIVER-BUILD-2","koronos_native_modules":["virtio","generic-vga"],"compatibility_payloads":["linux-firmware","linux .ko packages"],"requested_firmware":["firmware-iwlwifi","firmware-amd-graphics","firmware-atheros","firmware-brcm80211"],"firmware_snapshot":"${CHIMERA_LINUX_FIRMWARE_VERSION:-20260916}","linux_firmware_downloaded":"${CHIMERA_FETCH_LINUX_FIRMWARE:-0}"}
EOF
printf 'Driver payload staging complete: %s\n' "$OUT"
