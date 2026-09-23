#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="$ROOT/build/network-tools"
mkdir -p "$OUT/bin" "$OUT/rootfs" "$OUT/packages" "$OUT/manifests"

# APT must never write to the host package database/cache during ISO staging.
# Use a private APT state tree containing a read-only copy of the host indexes.
APT_ROOT="$OUT/.apt"
APT_STATE="$APT_ROOT/state"
APT_LISTS="$APT_STATE/lists"
APT_CACHE="$APT_ROOT/cache"
mkdir -p "$APT_LISTS/partial" "$APT_CACHE/archives/partial"

packages=(arping arp-scan fping netdiscover masscan nbtscan smbclient nfs-common rpcbind avahi-utils ldap-utils dnsutils curl wget openssh-client iproute2 iputils-ping net-tools traceroute zmap unicornscan snmp frr wireguard-tools openvpn)
if [ "${CHIMERA_NMAP_REDIStribute:-0}" = "1" ]; then
  packages+=(nmap)
fi

prepare_apt_sandbox() {
  # Copy only readable package indexes. They are treated as immutable input;
  # apt writes locks/cache files only under the private build directory.
  if [ -d /var/lib/apt/lists ]; then
    find /var/lib/apt/lists -maxdepth 1 -type f -readable -exec cp -f -- {} "$APT_LISTS/" \; 2>/dev/null || true
  fi

  # apt needs the Debian dpkg status database to resolve installed packages.
  # It is read-only and is never modified by this staging operation.
  if [ -r /var/lib/dpkg/status ]; then
    mkdir -p "$APT_STATE"
    cp -f /var/lib/dpkg/status "$APT_STATE/status"
  fi
}

download_packages() {
  local apt_opts=(
    "-o" "Debug::NoLocking=true"
    "-o" "Dir::State=$APT_STATE"
    "-o" "Dir::State::lists=$APT_LISTS"
    "-o" "Dir::State::status=$APT_STATE/status"
    "-o" "Dir::Cache=$APT_CACHE"
    "-o" "Dir::Cache::archives=$OUT/packages"
    "-o" "Dir::Cache::pkgcache=$APT_CACHE/pkgcache.bin"
    "-o" "Dir::Cache::srcpkgcache=$APT_CACHE/srcpkgcache.bin"
    "-o" "Dir::Etc::sourcelist=/etc/apt/sources.list"
    "-o" "Dir::Etc::sourceparts=/etc/apt/sources.list.d"
    "-o" "Acquire::Languages=none"
  )

  apt-get "${apt_opts[@]}" download "${packages[@]}"
}

if command -v apt-get >/dev/null 2>&1; then
  prepare_apt_sandbox
  (
    cd "$OUT/packages"
    if ! download_packages >/dev/null 2>&1; then
      echo "INFO package staging: sandboxed APT download unavailable or some packages are not configured; continuing with host tools." >&2
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
