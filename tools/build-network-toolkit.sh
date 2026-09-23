#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="$ROOT/build/network-tools"
mkdir -p "$OUT/bin" "$OUT/rootfs" "$OUT/packages" "$OUT/manifests"

packages=(arping arp-scan fping netdiscover masscan nbtscan smbclient nfs-common rpcbind avahi-utils ldap-utils dnsutils curl wget openssh-client iproute2 iputils-ping net-tools traceroute zmap unicornscan snmp frr wireguard-tools openvpn)
if [ "${CHIMERA_NMAP_REDIStribute:-0}" = "1" ]; then
  packages+=(nmap)
fi

download_packages() {
  local apt_opts=()
  # "apt-get download" is intentionally a non-root operation, but some apt
  # configurations still try to lock/update cache metadata. Disable locking
  # for this staging-only operation so ISO builds work from normal user shells.
  apt_opts+=("-o" "Debug::NoLocking=true")

  if apt-get download "${apt_opts[@]}" "${packages[@]}" >/dev/null 2>&1; then
    return 0
  fi

  # Some apt versions require the output directory to be the current working
  # directory and can leave partial downloads. Retry quietly; package staging
  # is best-effort because the host may not provide every package.
  return 1
}

if command -v apt-get >/dev/null 2>&1; then
  (
    cd "$OUT/packages"
    if ! download_packages; then
      echo "INFO package staging: apt download unavailable or some packages are not configured; continuing with host tools." >&2
    fi
  )
  for deb in "$OUT/packages/"*.deb; do
    [ -f "$deb" ] || continue
    dpkg-deb -x "$deb" "$OUT/rootfs" 2>/dev/null || true
  done
fi

for t in nmap ncat nping zmap unicornscan snmpwalk arping arp-scan fping netdiscover masscan nbtscan smbclient smbtree showmount rpcinfo avahi-browse ldapsearch dig curl wget ssh ip ss ping traceroute route; do
  if command -v "$t" >/dev/null 2>&1; then
    cp -L "$(command -v "$t")" "$OUT/bin/$t" 2>/dev/null || true
  fi
done

find "$OUT" -type f -print0 | sort -z | xargs -0r sha256sum > "$OUT/manifests/SHA256SUMS"
echo '{"schema":"CHM-NETWORK-TOOLKIT-BUILD-1","scope":"authorized local/intranet discovery","internet_scanning_default":false}' > "$OUT/manifests/network-toolkit.json"
echo "Network toolkit staged at $OUT"
