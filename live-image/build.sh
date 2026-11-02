#!/bin/bash
# Reproducible live-image builder for the Aurora/Octavian desktop stack.
#
#   ./build.sh chimera      # Chimera II OS live ISO
#   ./build.sh octavian     # OctavianOS live ISO
#
# Optional environment:
#   BUILD_ROOT=/path   where the rootfs/work/ISO output lives (default: live-image/.build)
#   JOBS=n             squashfs/xz CPU count (default: nproc)
#   SKIP_DEBOOTSTRAP=1 reuse an existing base rootfs
#
# Requires (Debian/Ubuntu host): debootstrap xorriso squashfs-tools grub-pc-bin
# grub-efi-amd64-bin mtools dosfstools imagemagick python3.
set -euo pipefail

ED="${1:-}"
case "$ED" in
  chimera|octavian) ;;
  *) echo "usage: $0 <chimera|octavian>"; exit 2 ;;
esac

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERE="$REPO_DIR/live-image"
BUILD="${BUILD_ROOT:-$HERE/.build}"
BASE="$BUILD/rootfs-base"
WORK="$BUILD/rootfs-$ED"
ISODIR="$BUILD/iso-$ED"
OUT="${OUT_DIR:-$BUILD/out}"
ART="$HERE/artwork"
JOBS="${JOBS:-$(nproc)}"

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -E bash "${BASH_SOURCE[0]}" "$@"
fi

case "$ED" in
  chimera)
    TITLE="Chimera II OS"
    SHORT="chimera-ii"
    VOLID="CHIMERA_II_OS"
    ENTRY="desktop/index.html"
    DESKTOP_COPY="web"
    ISO_NAME="chimera-ii-os-live-amd64.iso"
    ;;
  octavian)
    TITLE="OctavianOS"
    SHORT="octavian"
    VOLID="OCTAVIAN_OS"
    ENTRY="desktop/aurora-wayland-glass/index.html"
    DESKTOP_COPY="desktop"
    ISO_NAME="octavian-os-live-amd64.iso"
    ;;
esac
VERSION="$(date -u +%Y.%m.%d)"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo snapshot)"
BRANCH="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
REPO_URL="$(git -C "$REPO_DIR" config --get remote.origin.url 2>/dev/null | sed 's/\.git$//' || true)"
[ -n "$REPO_URL" ] || REPO_URL="https://github.com/amerhwitat/$(basename "$REPO_DIR")"

log() { printf '\n== [%s] %s\n' "$ED" "$*"; }

# ---------------------------------------------------------------- base rootfs
if [ ! -x "$BASE/bin/bash" ] || [ "${REBUILD_BASE:-0}" = "1" ]; then
  log "debootstrap trixie -> $BASE"
  rm -rf "$BASE"; mkdir -p "$BASE"
  debootstrap --arch=amd64 --variant=minbase \
    --include=apt-transport-https,ca-certificates,locales \
    trixie "$BASE" http://deb.debian.org/debian
fi

mount_chroot() {
  mkdir -p "$WORK/proc" "$WORK/sys" "$WORK/dev/pts"
  mountpoint -q "$WORK/proc"    || mount -t proc proc "$WORK/proc"
  mountpoint -q "$WORK/sys"     || mount -t sysfs sys "$WORK/sys"
  mountpoint -q "$WORK/dev"     || mount --bind /dev "$WORK/dev"
  mountpoint -q "$WORK/dev/pts" || mount --bind /dev/pts "$WORK/dev/pts"
  cp -f /etc/resolv.conf "$WORK/etc/resolv.conf"
}
umount_chroot() {
  for d in dev/pts dev sys proc; do
    mountpoint -q "$WORK/$d" && umount -l "$WORK/$d" || true
  done
}
trap umount_chroot EXIT

# ------------------------------------------------------------- package set
if [ ! -f "$BASE/.packages-installed" ]; then
  log "installing shared package set (one-off)"
  mount_chroot
  DEBIAN_FRONTEND=noninteractive chroot "$BASE" /bin/bash -c '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      linux-image-amd64 initramfs-tools live-boot live-boot-initramfs-tools \
      systemd systemd-sysv dbus dbus-x11 udev kbd console-setup \
      xserver-xorg-core xserver-xorg-legacy xserver-xorg-input-libinput \
      xserver-xorg-video-vesa xserver-xorg-video-fbdev xserver-xorg-video-cirrus \
      xinit xauth x11-xserver-utils x11-utils xfonts-base \
      python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
      libgl1 libglx-mesa0 libegl1 libgles2 \
      openbox xterm feh \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      sudo ca-certificates curl wget less nano htop pciutils usbutils file unzip xz-utils \
      iproute2 iputils-ping netbase procps psmisc rsync \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot
  touch "$BASE/.packages-installed"
fi

# ------------------------------------------------------------- rootfs copy
log "staging rootfs"
rm -rf "$WORK"; mkdir -p "$WORK"
tar -C "$BASE" -cf - --exclude=./proc --exclude=./sys --exclude=./dev --exclude=./run . \
  2>/dev/null | tar -C "$WORK" -xf - 2>/dev/null
mkdir -p "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run "$WORK"/tmp "$WORK"/mnt "$WORK"/media

# ------------------------------------------------------------- payload
log "staging payload"
PAY="$WORK/opt/aurora"
rm -rf "$PAY"; mkdir -p "$PAY/wallpapers"
cp -a "$REPO_DIR/$DESKTOP_COPY" "$PAY/desktop"
[ "$ED" = "octavian" ] && cp -a "$REPO_DIR/apps" "$PAY/apps"

python3 - "$ART" "$PAY" <<'PY'
import json, os, subprocess, sys
src, pay = sys.argv[1], sys.argv[2]
manifest = json.load(open(os.path.join(src, "manifest.json")))
out = []
for item in manifest:
    dst = os.path.join(pay, "wallpapers", item["file"])
    subprocess.run(["convert", os.path.join(src, item["file"]),
                    "-resize", "2560x2560>", "-strip", "-quality", "88", dst], check=True)
    out.append({"name": item["name"], "file": item["file"], "source": item.get("source", "")})
json.dump(out, open(os.path.join(pay, "wallpapers", "index.json"), "w"), indent=1)
print("wallpapers:", len(out))
PY

# verbatim source snapshot for provenance (excluding build output)
mkdir -p "$PAY/repo"
tar -C "$REPO_DIR" --exclude=./.git --exclude=./live-image/.build -cf - . 2>/dev/null \
  | tar -C "$PAY/repo" -xf - 2>/dev/null || true

python3 "$HERE/lib/patch_html.py" "$PAY/$ENTRY" "$PAY" wp01.jpg

cat > "$PAY/PROJECT.md" <<EOF
# $TITLE live image payload

- Upstream: $REPO_URL
- Branch: $BRANCH
- Commit: $COMMIT
- Build date: $VERSION (UTC)
- Volume label: $VOLID

\`desktop/\` is the project's own HTML desktop, rendered fullscreen by the Aurora kiosk
shell (WebKit2GTK). \`wallpapers/\` holds the artwork shipped with this build, wired into
every page's background picker. \`repo/\` is a verbatim snapshot of the source tree.

The image boots a Linux kernel: the project's native Spit Fire/Koronos kernel is
documented upstream as not yet reaching a verified userspace handoff.
EOF

cat > "$PAY/README.txt" <<EOF
$TITLE live image — $VERSION
===============================
Desktop : $ENTRY (fullscreen kiosk)
Keys    : Ctrl+Q quit kiosk · Ctrl+R reload · Ctrl+Alt+F2 text console
Console : login live / live (passwordless sudo)
Menu    : "Classic X session" boots openbox + xterm
Artwork : /opt/aurora/wallpapers and /usr/share/backgrounds/$SHORT
Source  : $REPO_URL
EOF

# ------------------------------------------------------------- system config
log "system configuration"
install -Dm755 "$HERE/lib/aurora-kiosk.py" "$WORK/usr/local/bin/aurora-kiosk.py"

cat > "$WORK/usr/local/bin/aurora-session" <<'EOF'
#!/bin/bash
# Session entry point started from the tty1 autologin.
export LIBGL_ALWAYS_SOFTWARE=1
export WEBKIT_DISABLE_COMPOSITING_MODE=1
export WEBKIT_DISABLE_DMABUF_RENDERER=1
export GDK_BACKEND=x11
export XDG_RUNTIME_DIR=/tmp/runtime-live
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
xsetroot -solid "#071a2b" 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s off 2>/dev/null || true
if grep -q "session=classic" /proc/cmdline 2>/dev/null; then
  for w in /usr/share/backgrounds/*/wp01.jpg; do [ -f "$w" ] && feh --bg-fill "$w"; done
  exec openbox
fi
exec /usr/bin/python3 /usr/local/bin/aurora-kiosk.py
EOF
echo "export AURORA_DESKTOP_URI=file:///opt/aurora/$ENTRY" >> "$WORK/usr/local/bin/aurora-session"
chmod 755 "$WORK/usr/local/bin/aurora-session"

printf '#!/bin/sh\nexec /usr/local/bin/aurora-session\n' > "$WORK/etc/xinitrc"
chmod 755 "$WORK/etc/xinitrc"

chroot "$WORK" /bin/bash -c "
  set -e
  id live >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash -G sudo,video,audio,input live
  echo 'live:live' | chpasswd
  echo 'root:live' | chpasswd
"
echo 'live ALL=(ALL) NOPASSWD:ALL' > "$WORK/etc/sudoers.d/90-live"
chmod 440 "$WORK/etc/sudoers.d/90-live"

cp "$WORK/etc/xinitrc" "$WORK/home/live/.xinitrc"
cat > "$WORK/home/live/.bash_profile" <<'EOF'
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx
fi
EOF
chown 1000:1000 "$WORK/home/live/.xinitrc" "$WORK/home/live/.bash_profile"

install -d "$WORK/etc/systemd/system/getty@tty1.service.d"
printf '[Service]\nExecStart=\nExecStart=-/sbin/agetty --autologin live --noclear %%I $TERM\nType=simple\n' \
  > "$WORK/etc/systemd/system/getty@tty1.service.d/autologin.conf"

cat > "$WORK/etc/os-release" <<EOF
PRETTY_NAME="$TITLE $VERSION (live)"
NAME="$TITLE"
VERSION="$VERSION"
ID=$SHORT
VERSION_ID=$VERSION
HOME_URL="$REPO_URL"
EOF
cat > "$WORK/etc/issue" <<EOF

  $TITLE $VERSION  ·  live image (x86_64)
  $REPO_URL @ $COMMIT

EOF

echo "$SHORT" > "$WORK/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 %s\n::1 localhost ip6-localhost ip6-loopback\n' "$SHORT" > "$WORK/etc/hosts"

ln -sfn /lib/systemd/system/multi-user.target "$WORK/etc/systemd/system/default.target"
mkdir -p "$WORK/etc/systemd/network" \
         "$WORK/etc/systemd/system/multi-user.target.wants" \
         "$WORK/etc/systemd/system/sockets.target.wants"
printf '[Match]\nName=e*\n[Network]\nDHCP=yes\n' > "$WORK/etc/systemd/network/20-wired.network"
ln -sfn /lib/systemd/system/systemd-networkd.service \
  "$WORK/etc/systemd/system/multi-user.target.wants/systemd-networkd.service"
ln -sfn /lib/systemd/system/systemd-networkd.socket \
  "$WORK/etc/systemd/system/sockets.target.wants/systemd-networkd.socket"

mkdir -p "$WORK/usr/share/backgrounds/$SHORT"
cp -a "$PAY/wallpapers/." "$WORK/usr/share/backgrounds/$SHORT/"

printf 'MODULES=most\nCOMPRESS=gzip\n' > "$WORK/etc/initramfs-tools/conf.d/live.conf"
chroot "$WORK" /bin/bash -c "update-initramfs -u -k all" >/dev/null

# ------------------------------------------------------------- shrink
log "trimming"
rm -rf "$WORK"/usr/share/doc/* "$WORK"/usr/share/man/* "$WORK"/usr/share/info/* 2>/dev/null || true
rm -rf "$WORK"/usr/share/fonts/truetype/noto "$WORK"/usr/share/fonts/opentype/noto* 2>/dev/null || true
find "$WORK/usr/share/locale" -mindepth 1 -maxdepth 1 -type d ! -name 'en*' -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORK"/usr/share/i18n/locales/* 2>/dev/null || true
rm -rf "$WORK"/var/log/* "$WORK"/var/cache/* "$WORK"/tmp/* "$WORK"/usr/lib/debug 2>/dev/null || true

# ------------------------------------------------------------- squashfs + ISO
log "squashfs"
mkdir -p "$ISODIR/live" "$OUT"
rm -f "$ISODIR/live/filesystem.squashfs"
mksquashfs "$WORK" "$ISODIR/live/filesystem.squashfs" \
  -comp xz -Xbcj x86 -b 1M -noappend -processors "$JOBS"

log "boot files"
cp "$WORK"/boot/vmlinuz-* "$ISODIR/live/vmlinuz"
cp "$WORK"/boot/initrd.img-* "$ISODIR/live/initrd.img"
mkdir -p "$ISODIR/boot/grub"
convert "$ART/wp03.jpg" -resize 1920x1080^ -gravity center -extent 1920x1080 \
  -strip -quality 90 "$ISODIR/boot/grub/background.jpg"

cat > "$ISODIR/boot/grub/grub.cfg" <<EOF
set default=0
set timeout=10
insmod all_video
insmod gfxterm
insmod png
insmod jpeg
insmod font
set gfxmode=1920x1080,1280x1024,1024x768,auto
set gfxpayload=keep
terminal_output gfxterm
if [ -f /boot/grub/background.jpg ]; then background_image /boot/grub/background.jpg; fi

menuentry "$TITLE $VERSION — Live desktop" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Classic X session (openbox)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live session=classic quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Safe graphics (nomodeset)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live nomodeset quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Verbose boot" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live
  initrd /live/initrd.img
}
menuentry "Reboot" { reboot }
menuentry "Power off" { halt }
EOF

log "iso"
rm -f "$OUT/$ISO_NAME"
grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
