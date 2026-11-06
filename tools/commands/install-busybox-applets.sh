#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: install-busybox-applets.sh ROOTFS}"
[[ -d "$ROOTFS" && -x "$ROOTFS/bin/sh" ]] || { echo "invalid rootfs: $ROOTFS" >&2; exit 2; }
BB="$(chroot "$ROOTFS" /bin/sh -c 'command -v busybox' 2>/dev/null || true)"
[[ -n "$BB" ]] || { echo "target rootfs has no BusyBox executable" >&2; exit 2; }
install -d "$ROOTFS/usr/local/bin" "$ROOTFS/usr/share/chimera/commands"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
chroot "$ROOTFS" "$BB" --list > "$tmp"
manifest="$ROOTFS/usr/share/chimera/commands/busybox-applets.tsv"
: > "$manifest"
while IFS= read -r applet; do
  [[ -n "$applet" && "$applet" != */* ]] || continue
  if chroot "$ROOTFS" /bin/sh -c "command -v '$applet' >/dev/null 2>&1"; then
    continue
  fi
  link="$ROOTFS/usr/local/bin/$applet"
  [[ ! -e "$link" && ! -L "$link" ]] || continue
  ln -s "$BB" "$link"
  printf '%s|/usr/local/bin/%s|busybox-static\n' "$applet" "$applet" >> "$manifest"
done < "$tmp"
printf 'Installed %s BusyBox applet links without overwriting existing providers.\n' "$(wc -l < "$manifest")"
