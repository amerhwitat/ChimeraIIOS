#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="$ROOT/build/network-tools"
mkdir -p "$OUT"/bin "$OUT"/rootfs "$OUT"/packages "$OUT"/manifests
packages=(nmap arping arp-scan fping netdiscover masscan nbtscan smbclient nfs-common rpcbind avahi-utils ldap-utils dnsutils curl wget openssh-client iproute2 iputils-ping net-tools traceroute)
if command -v apt-get >/dev/null 2>&1; then
  (cd "$OUT/packages"; apt-get download "${packages[@]}" >/dev/null 2>&1 || true)
  for deb in "$OUT/packages/"*.deb; do [ -f "$deb" ] || continue; dpkg-deb -x "$deb" "$OUT/rootfs" 2>/dev/null || true; done
fi
for t in nmap ncat nping arping arp-scan fping netdiscover masscan nbtscan smbclient smbtree showmount rpcinfo avahi-browse ldapsearch dig curl wget ssh ip ss ping traceroute route; do
  if command -v "$t" >/dev/null 2>&1; then cp -L "$(command -v "$t")" "$OUT/bin/$t" 2>/dev/null || true; fi
done
find "$OUT" -type f -print0 | sort -z | xargs -0r sha256sum > "$OUT/manifests/SHA256SUMS"
echo '{"schema":"CHM-NETWORK-TOOLKIT-BUILD-1","scope":"authorized local/intranet discovery","internet_scanning_default":false}' > "$OUT/manifests/network-toolkit.json"
echo "Network toolkit staged at $OUT"
