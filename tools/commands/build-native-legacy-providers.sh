#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="\${1:?target rootfs required}"
REPO_ROOT="\${2:-/opt/aurora/repo}"
SOURCE="$REPO_ROOT/tools/commands/native"
DEST="$ROOTFS/usr/local/bin"
mkdir -p "$DEST"
for source in write.c fdformat.c; do
  [[ -s "$SOURCE/$source" ]] || { echo "missing native command source: $SOURCE/$source" >&2; exit 2; }
done
chroot "$ROOTFS" /usr/bin/gcc -std=c11 -O2 -Wall -Wextra -Werror -D_DEFAULT_SOURCE \\
  "/opt/aurora/repo/tools/commands/native/write.c" -o /usr/local/bin/write
chroot "$ROOTFS" /usr/bin/gcc -std=c11 -O2 -Wall -Wextra -Werror -D_DEFAULT_SOURCE \\
  "/opt/aurora/repo/tools/commands/native/fdformat.c" -o /usr/local/bin/fdformat
echo "[COMMAND-NATIVE] built write and fdformat from source"
