#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="$ROOT/build/network-tools"
mkdir -p "$OUT/bin" "$OUT/rootfs" "$OUT/packages" "$OUT/manifests"
APT_CACHE="$OUT/.apt-cache"
APT_LISTS="$OUT/.apt-lists"
mkdir -p "$APT_CACHE/archives/partial" "$APT_LISTS/partial"

packages=(arping arp-scan fping netdiscover masscan nbtscan smbclient nfs-common rpcbind avahi-utils ldap-utils dnsutils curl wget openssh-client iproute2 iputils-ping net-tools traceroute zmap unicornscan snmp frr wireguard-tools openvpn)
if [ "${CHIMERA_NMAP_REDIStribute:-0}" = "1" ]; then
  packages+=(nmap)
fi

download_packages() {
  # Never modify or lock the host APT state/cache.  The package indexes remain
  # read-only under /var/lib/apt/lists; all writable APT state is redirected
  # into the build tree so this script works from an ordinary user shell.
  local apt_opts=(
    "-o" "Debug::NoLocking=true"
    "-o" "Dir::Cache=$APT_CACHE"
    "-o" "Dir::Cache::archives=$OUT/packages"
    "-o" "Dir::Cache::pkgcache=$APT_CACHE/pkgcache.bin"
    "-o" "Dir::Cache::srcpkgcache=$APT_CACHE/srcpkgcache.bin"
    "-o" "Dir::State::lists=/var/lib/apt/lists"
  )

  # Options must precede the apt command.  Putting them after "download" makes
  # apt-get parse them as package arguments on some apt versions.
  apt-get "${apt_opts[@]}" download "${packages[@]}"
}

if command -v apt-get >/dev/null 2>&1; then
  (
    cd "$OUT/packages"
    if ! download_packages >/dev/null 2>&1; then
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
