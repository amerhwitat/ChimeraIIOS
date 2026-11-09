#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
rootfs="$tmp/rootfs"
mkdir -p "$rootfs/usr/bin" "$rootfs/usr/local/bin"
for command in lprm lpq plocate; do
  cat > "$rootfs/usr/bin/$command" <<'PROVIDER'
#!/bin/sh
printf '%s\n' "$(basename "$0"):$*"
PROVIDER
  chmod 0755 "$rootfs/usr/bin/$command"
done
bash "$ROOT/tools/commands/install-legacy-command-compat.sh" "$rootfs"
PATH="$rootfs/usr/bin:$PATH"
[[ "$("$rootfs/usr/local/bin/lprintd" 17)" == "lprm:17" ]]
[[ "$("$rootfs/usr/local/bin/lprintq" -P office)" == "lpq:-P office" ]]
[[ "$("$rootfs/usr/local/bin/slocate" -i report)" == "plocate:-i report" ]]

sparse="$tmp/sparse.bin"
"$rootfs/usr/local/bin/mkfile" -n 2k "$sparse"
[[ "$(stat -c %s "$sparse")" -eq 2048 ]]
[[ "$(stat -c %b "$sparse")" -eq 0 ]]

allocated="$tmp/allocated.bin"
"$rootfs/usr/local/bin/mkfile" -v 1k "$allocated" > "$tmp/mkfile.out"
[[ "$(stat -c %s "$allocated")" -eq 1024 ]]
[[ -k "$allocated" ]]
grep -q 'allocated.bin: 1024 bytes' "$tmp/mkfile.out"
echo "Legacy command compatibility providers: PASS"
