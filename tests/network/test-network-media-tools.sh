#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
for f in "$ROOT/tools/network/chimera-network-browser.sh" "$ROOT/tools/storage/chimera-media-mount.sh" "$ROOT/tools/storage/chimera-init-layout.sh"; do
  bash -n "$f"
  bash "$f" --help >/dev/null
done
grep -q 'client min protocol=SMB2' "$ROOT/tools/network/chimera-network-browser.sh"
grep -q 'ldaps://' "$ROOT/tools/network/chimera-network-browser.sh"
grep -q 'nodev,nosuid,noexec' "$ROOT/tools/storage/chimera-media-mount.sh"
grep -q 'iso9660' "$ROOT/tools/storage/chimera-media-mount.sh"
echo "PASS: network, directory-service and optical-media static checks"
