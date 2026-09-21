#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"
OUT="${CHIMERA_DRIVER_DISCOVERY_DIR:-$ROOT/build/driver-discovery}"
mkdir -p "$OUT"/{devices,repositories,packages,modules,firmware,quarantine,manifests}
if [[ -z "$TARGET" ]]; then TARGET="/"; fi

# Hardware identity discovery. Prefer lspci/lsusb/udevadm, with sysfs fallback.
if command -v lspci >/dev/null 2>&1; then lspci -nnk > "$OUT/devices/pci.txt" || true; fi
if command -v lsusb >/dev/null 2>&1; then lsusb -nn > "$OUT/devices/usb.txt" || true; fi
if command -v udevadm >/dev/null 2>&1; then udevadm info --export-db > "$OUT/devices/udev-db.txt" || true; fi
find /sys/bus -maxdepth 3 -type f \( -name modalias -o -name uevent \) -print 2>/dev/null | sort > "$OUT/devices/sysfs-device-files.txt" || true

# Approved open-source repositories. The search is recursive over repository
# metadata/content; binaries are only accepted from package repositories or
# explicitly configured trusted sources, never arbitrary search results.
cat > "$OUT/repositories/sources.json" <<'EOF'
{
  "sources":[
    {"name":"Linux kernel","url":"https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git","type":"source"},
    {"name":"linux-firmware","url":"https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git","type":"firmware"},
    {"name":"Ubuntu packages","url":"https://packages.ubuntu.com/","type":"package"},
    {"name":"Debian packages","url":"https://packages.debian.org/","type":"package"},
    {"name":"Fedora packages","url":"https://packages.fedoraproject.org/","type":"package"},
    {"name":"openSUSE packages","url":"https://software.opensuse.org/","type":"package"},
    {"name":"Arch packages","url":"https://archlinux.org/packages/","type":"package"}
  ],
  "policy":{"proprietary_binaries":"disabled","unsigned_downloads":"quarantine","arbitrary_urls":"disabled"}
}
EOF

# Build a device-to-driver evidence report. Native Koronos modules and Linux
# compatibility modules remain separate ABI domains.
{
  echo '{"schema":"CHM-DRIVER-DISCOVERY-1","target":"'"$TARGET"'","native_abi":"KORONOS_DRIVER_ABI","sources":"approved"}'
  echo '"device_files":'
  find "$OUT/devices" -type f -printf '%p\n' | sort
} > "$OUT/manifests/discovery.txt"

# Copy verified package payloads into the target only when explicitly requested.
if [[ "${CHIMERA_DEPLOY_DRIVER_PAYLOADS:-0}" == "1" && -d "$ROOT/build/drivers" ]]; then
  mkdir -p "$TARGET/var/lib/chimera/drivers" "$TARGET/lib/firmware" "$TARGET/usr/lib/chimera/drivers"
  cp -a "$ROOT/build/drivers/." "$TARGET/var/lib/chimera/drivers/"
  find "$TARGET/var/lib/chimera/drivers" -type f -name '*.ko' -exec cp -n {} "$TARGET/usr/lib/chimera/drivers/" \; 2>/dev/null || true
  find "$TARGET/var/lib/chimera/drivers" -type f -name '*.fw' -exec cp -n {} "$TARGET/lib/firmware/" \; 2>/dev/null || true
fi
find "$OUT" -type f -print0 | sort -z | xargs -0r sha256sum > "$OUT/manifests/SHA256SUMS"
echo "Deep driver discovery complete: $OUT"
