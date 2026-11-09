#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: install-busybox-applets.sh ROOTFS}"
[[ -d "$ROOTFS" && -x "$ROOTFS/bin/sh" ]] || { echo "invalid rootfs: $ROOTFS" >&2; exit 2; }
# Resolve the binary by its target-rootfs path instead of relying on the
# target shell's PATH (which may itself be a BusyBox applet symlink during
# initramfs construction).
BB=""
for candidate in /bin/busybox /usr/bin/busybox /usr/local/bin/busybox; do
  if [[ -x "$ROOTFS$candidate" && ! -L "$ROOTFS$candidate" ]]; then
    BB="$candidate"
    break
  fi
done
[[ -n "$BB" ]] || { echo "target rootfs has no regular executable BusyBox binary in /bin, /usr/bin or /usr/local/bin" >&2; exit 2; }
install -d "$ROOTFS/usr/local/bin" "$ROOTFS/usr/share/chimera/commands"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
chroot "$ROOTFS" "$BB" --list > "$tmp"
manifest="$ROOTFS/usr/share/chimera/commands/busybox-applets.tsv"
: > "$manifest"
while IFS= read -r applet; do
  [[ -n "$applet" && "$applet" != */* ]] || continue
  existing="$(chroot "$ROOTFS" /bin/sh -c "command -v '$applet' 2>/dev/null || true")"
  if [[ -n "$existing" ]]; then
    if [[ "$(readlink -f "$ROOTFS$existing" 2>/dev/null || true)" == "$(readlink -f "$ROOTFS$BB")" ]]; then
      printf '%s|%s|busybox-static\n' "$applet" "$existing" >> "$manifest"
    fi
    continue
  fi
  link="$ROOTFS/usr/local/bin/$applet"
  [[ ! -e "$link" && ! -L "$link" ]] || continue
  ln -s "$BB" "$link"
  printf '%s|/usr/local/bin/%s|busybox-static\n' "$applet" "$applet" >> "$manifest"
done < "$tmp"
printf 'Installed %s BusyBox applet links without overwriting existing providers.\n' "$(wc -l < "$manifest")"
