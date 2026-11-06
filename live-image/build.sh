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
python3 "$REPO_DIR/tools/boot/verify-menu-timeouts.py" --root "$REPO_DIR"
HERE="$REPO_DIR/live-image"
BUILD="${BUILD_ROOT:-$HERE/.build}"
NATIVE_COMMAND_OUT="$BUILD/native-command-isa"
BASE="$BUILD/rootfs-base"
WORK="${WORK_DIR:-$BUILD/rootfs-$ED}"
ISODIR="$BUILD/iso-$ED"
OUT="${OUT_DIR:-$BUILD/out}"
ART="$HERE/artwork"
JOBS="${JOBS:-$(nproc)}"

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -E bash "${BASH_SOURCE[0]}" "$@"
fi
# Build target-specific native command binaries for both hosted desktop editions.
python3 "$REPO_DIR/tools/commands/build_native_command_matrix.py" \
  --source "$REPO_DIR/src/chimera-command-compat/chimera-cmd.c" \
  --policy "$REPO_DIR/system/commands/compatibility-binary-policy.json" \
  --output "$NATIVE_COMMAND_OUT" \
  --require-all
bash "$REPO_DIR/tests/commands/test-native-command-matrix.sh" "$NATIVE_COMMAND_OUT"

case "$ED" in
  chimera)
    TITLE="Chimera II OS"
    SHORT="chimera-ii"
    VOLID="CHIMERA_II_OS"
    ENTRY="desktop/aurora-shell/index.html"
    DESKTOP_COPY="web"
    ISO_NAME="chimera-ii-os-live-amd64.iso"
    ;;
  octavian)
    TITLE="OctavianOS"
    SHORT="octavian"
    VOLID="OCTAVIAN_OS"
    ENTRY="desktop/aurora-shell/index.html"
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
  local T="${1:-$WORK}"
  mkdir -p "$T/proc" "$T/sys" "$T/dev/pts"
  mountpoint -q "$T/proc"    || mount -t proc proc "$T/proc"
  mountpoint -q "$T/sys"     || mount -t sysfs sys "$T/sys"
  mountpoint -q "$T/dev"     || mount --bind /dev "$T/dev"
  mountpoint -q "$T/dev/pts" || mount --bind /dev/pts "$T/dev/pts"
  cp -f /etc/resolv.conf "$T/etc/resolv.conf"
}
umount_chroot() {
  local T="${1:-$WORK}"
  for d in dev/pts dev sys proc; do
    mountpoint -q "$T/$d" && umount -l "$T/$d" || true
  done
}
trap 'umount_chroot "$WORK"; umount_chroot "$BASE"' EXIT

# ------------------------------------------------------------- package set
if [ ! -f "$BASE/.packages-installed" ]; then
  log "installing shared package set (one-off)"
  mount_chroot "$BASE"
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
      libgl1 libglx-mesa0 libegl1 libgles2 libgl-dev libegl-dev libgles-dev \
      libgbm1 libgl1-mesa-dri mesa-utils \
      openbox xterm feh \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      busybox-static coreutils findutils grep sed gawk util-linux procps psmisc \
      iproute2 iputils-ping net-tools dnsutils traceroute openssh-client \
      sudo login passwd file tree plocate lsof strace bc acl \
      ca-certificates curl wget less nano htop jq git rsync \
      tar gzip bzip2 xz-utils zip unzip man-db manpages \
      gcc g++ make cmake ninja-build meson gdb python3 python3-pip perl ruby nodejs npm \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  touch "$BASE/.packages-installed"
fi

# ------------------------------------------------------------- rootfs copy
log "staging rootfs"
rm -rf "$WORK"; mkdir -p "$WORK"
# cp -a keeps ownership/modes and is markedly faster than a tar pipe on this
# tree; device nodes cannot be recreated without CAP_MKNOD, so /dev, /proc and
# /sys are rebuilt empty (the initramfs mounts their filesystems).
cp -a "$BASE/." "$WORK/" 2>/dev/null || true
rm -rf "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run
mkdir -p "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run "$WORK"/tmp "$WORK"/mnt "$WORK"/media

# Install every BusyBox applet as a real multicall command where no native
# package binary already exists. Never replace a GNU/coreutils implementation.
BB_IN_ROOT=""
for candidate in /bin/busybox /usr/bin/busybox; do
  if [[ -x "$WORK$candidate" ]]; then BB_IN_ROOT="$candidate"; break; fi
done
if [[ -z "$BB_IN_ROOT" ]]; then
  echo "[ERROR] busybox-static was not installed in the live rootfs" >&2
  exit 2
fi
while IFS= read -r applet; do
  [[ -n "$applet" && "$applet" != */* && "$applet" != "busybox" ]] || continue
  if [[ ! -e "$WORK/usr/bin/$applet" && ! -e "$WORK/bin/$applet" ]]; then
    ln -s /bin/busybox "$WORK/usr/bin/$applet"
  fi
done < <("$WORK$BB_IN_ROOT" --list)

# Put the complete command/ISA catalogues and the actual provider coverage
# report in both desktop editions; catalog-only entries remain explicitly marked.
install -d "$WORK/usr/share/chimera/catalogs"
for rel in system/commands/chimera-command-list.json config/linux-command-registry.json tools/commands/os-command-runtime.json ISA.csv data/isa/online-isa-index.json; do
  if [[ -s "$REPO_DIR/$rel" ]]; then install -D -m 0644 "$REPO_DIR/$rel" "$WORK/usr/share/chimera/catalogs/$(basename "$rel")"; fi
done
install -d "$WORK/usr/lib/chimera/commands/native"
cp -a "$NATIVE_COMMAND_OUT/." "$WORK/usr/lib/chimera/commands/native/"
python3 "$REPO_DIR/tools/commands/build-command-isa-coverage.py" \
  --root "$REPO_DIR" --busybox "$WORK$BB_IN_ROOT" \
  --native-matrix "$NATIVE_COMMAND_OUT/manifest.json" \
  --output "$WORK/usr/share/chimera/catalogs/command-isa-coverage.json"

# Install a diagnostic for the shared Mesa/OpenGL/EGL/GLES stack.
install -D -m 0755 "$REPO_DIR/tools/graphics/verify-opengl-runtime.sh" "$WORK/usr/local/bin/chimera-verify-opengl"
# Install the optional Aurora event sound player and start cue after sound.target.
install -D -m 0755 "$REPO_DIR/desktop/aurora/aurora-event-sound.sh" "$WORK/usr/local/bin/aurora-event-sound"
install -d "$WORK/etc/systemd/system/multi-user.target.wants"
cat > "$WORK/etc/systemd/system/aurora-startup-sound.service" <<'UNIT'
[Unit]
Description=Aurora desktop startup sound
After=sound.target
Wants=sound.target

[Service]
Type=oneshot
User=live
Environment=CHIMERA_SOUND_DIR=/usr/share/chimera/aurora/sounds
Environment=CHIMERA_SOUND_VOLUME=0.55
ExecStart=/usr/local/bin/aurora-event-sound startup

[Install]
WantedBy=multi-user.target
UNIT
ln -sfn ../aurora-startup-sound.service "$WORK/etc/systemd/system/multi-user.target.wants/aurora-startup-sound.service"

# Install real, package-manager-verified open-source shells and terminals in both editions.
log "installing Aurora terminal and shell suite"
bash "$REPO_DIR/tools/aurora/install-terminal-shell-suite.sh" "$WORK"
bash "$REPO_DIR/tools/aurora/build-terminal-shell-sources.sh" "$WORK" "$BUILD/terminal-shell-sources"

# ------------------------------------------------------------- payload
log "staging payload"
PAY="$WORK/opt/aurora"
rm -rf "$PAY"; mkdir -p "$PAY/wallpapers"

# Build and install every generated Aurora visual asset for both OS editions.
AURORA_MEDIA="$BUILD/aurora-media-$ED"
bash "$REPO_DIR/tools/aurora/build-visual-assets.sh" "$AURORA_MEDIA"
install -d "$WORK/usr/share/chimera/aurora/media" "$WORK/usr/share/chimera/aurora/icons"
cp -a "$AURORA_MEDIA/." "$WORK/usr/share/chimera/aurora/media/"
python3 "$REPO_DIR/tools/aurora/export-icon-theme.py" \
  --output "$BUILD/aurora-icons-$ED"
install -d "$WORK/usr/share/icons/hicolor/scalable/apps" "$WORK/usr/share/icons/chimera-aurora/scalable/apps"
cp -a "$BUILD/aurora-icons-$ED/." "$WORK/usr/share/icons/chimera-aurora/"
cp -a "$BUILD/aurora-icons-$ED/chimera-"*.svg "$WORK/usr/share/icons/hicolor/scalable/apps/"
cp -a "$BUILD/aurora-icons-$ED/chimera-"*.svg "$WORK/usr/share/icons/chimera-aurora/scalable/apps/"
install -d "$WORK/etc/gtk-3.0"
cat > "$WORK/etc/gtk-3.0/settings.ini" <<'GTK'
[Settings]
gtk-icon-theme-name=chimera-aurora
GTK
cp -a "$REPO_DIR/desktop/aurora/assets/sounds" "$WORK/usr/share/chimera/aurora/"
cp -a "$REPO_DIR/desktop/aurora/icons/icon_theme.json" "$WORK/usr/share/chimera/aurora/icons/"
cp -a "$REPO_DIR/$DESKTOP_COPY" "$PAY/desktop"
# Ship the complete 133-icon original artwork sprite and native hicolor icon files.
mkdir -p "$PAY/desktop/app-icons"
cp -f "$REPO_DIR/desktop/app-icons/catalog.svg" "$PAY/desktop/app-icons/catalog.svg"
cp -f "$REPO_DIR/desktop/app-icons/manifest.json" "$PAY/desktop/app-icons/manifest.json"
python3 "$REPO_DIR/tools/aurora/export-app-icon-theme.py" \
  --sprite "$REPO_DIR/desktop/app-icons/catalog.svg" \
  --manifest "$REPO_DIR/desktop/app-icons/manifest.json" \
  --output "$WORK/usr/share/icons/hicolor/scalable/apps"
cat > "$WORK/usr/share/icons/hicolor/index.theme" <<'THEME'
[Icon Theme]
Name=hicolor
Comment=Fallback icon theme with Chimera Aurora app artwork
Directories=scalable/apps
[scalable/apps]
Size=64
Type=Scalable
MinSize=16
MaxSize=256
THEME

# Publish desktop launchers only for executables actually present in this rootfs.
CHIMERA_ROOTFS_DIR="$WORK" bash "$REPO_DIR/aurora/terminals/install-desktop-entries.sh"

# Aurora desktop shell (multi-profile window manager + apps) for every edition.
if [ -d "$REPO_DIR/desktop/aurora-shell" ]; then
  mkdir -p "$PAY/desktop"
  cp -a "$REPO_DIR/desktop/aurora-shell" "$PAY/desktop/aurora-shell"
  # The shell resolves audio files relative to desktop/aurora-shell/index.html.
  install -d "$PAY/desktop/aurora/assets"
  cp -a "$REPO_DIR/desktop/aurora/assets/sounds" "$PAY/desktop/aurora/assets/sounds"
fi
[ "$ED" = "octavian" ] && cp -a "$REPO_DIR/apps" "$PAY/apps"

python3 - "$ART" "$PAY" "$AURORA_MEDIA" <<'PY'
import json, os, shutil, subprocess, sys
src, pay, media = sys.argv[1:4]
wallpapers = os.path.join(pay, "wallpapers")
manifest = json.load(open(os.path.join(src, "manifest.json"), encoding="utf-8"))
out = []
for item in manifest:
    dst = os.path.join(wallpapers, item["file"])
    subprocess.run(["convert", os.path.join(src, item["file"]),
                    "-resize", "2560x2560>", "-strip", "-quality", "88", dst], check=True)
    out.append({"name": item["name"], "file": item["file"], "url": item["file"],
                "source": item.get("source", "")})
# Add every generated Aurora screen/background to the desktop wallpaper picker.
visual = json.load(open(os.path.join(media, "manifest.json"), encoding="utf-8"))
for role, rel in visual.get("assets", {}).items():
    source = os.path.join(media, rel)
    if not os.path.isfile(source):
        raise SystemExit(f"generated Aurora visual is missing: {source}")
    filename = "aurora-" + os.path.basename(rel)
    destination = os.path.join(wallpapers, filename)
    shutil.copy2(source, destination)
    out.append({"name": "Aurora " + role.replace("_", " ").title(),
                "file": filename, "url": filename, "source": "generated:" + rel,
                "role": role})
video = os.path.join(media, "Init.mp4")
if os.path.isfile(video):
    shutil.copy2(video, os.path.join(wallpapers, "aurora-init.mp4"))
json.dump(out, open(os.path.join(wallpapers, "index.json"), "w", encoding="utf-8"), indent=1)
print("wallpapers:", len(out), "(repository + generated Aurora artwork)")
PY

# verbatim source snapshot for provenance (excluding build output)
mkdir -p "$PAY/repo"
tar -C "$REPO_DIR" --exclude=./.git --exclude=./live-image/.build -cf - . 2>/dev/null \
  | tar -C "$PAY/repo" -xf - 2>/dev/null || true

# Stage every repository-owned application catalog for offline discovery.
# Catalog-only upstream references remain distinct from installed executables.
mkdir -p "$PAY/app-catalogs" "$PAY/apps/native/aurora"
stage_catalog() {
  local rel="$1"
  if [ -f "$REPO_DIR/$rel" ]; then
    mkdir -p "$PAY/app-catalogs/$(dirname "$rel")"
    cp -f "$REPO_DIR/$rel" "$PAY/app-catalogs/$rel"
  fi
}
for rel in \
  applications/catalog.json \
  desktop/optional_apps_catalog.json \
  appcenter/catalog/apps.json \
  appcenter/catalog/external-integrations.json \
  iso/manifests/application-catalog.txt \
  apps/desktop-application-catalog.json; do
  stage_catalog "$rel"
done
if [ "$ED" = "octavian" ]; then
  for rel in \
    vendor/chimera-ii-os/source/applications/catalog.json \
    vendor/chimera-ii-os/source/desktop/optional_apps_catalog.json \
    vendor/chimera-ii-os/source/appcenter/catalog/apps.json \
    vendor/chimera-ii-os/source/appcenter/catalog/external-integrations.json \
    vendor/chimera-ii-os/source/iso/manifests/application-catalog.txt; do
    stage_catalog "$rel"
  done
  if [ -d "$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/apps" ]; then
    cp -a "$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/apps/." "$PAY/apps/native/aurora/"
  fi
else
  if [ -d "$REPO_DIR/desktop/aurora/apps" ]; then
    cp -a "$REPO_DIR/desktop/aurora/apps/." "$PAY/apps/native/aurora/"
  fi
  mkdir -p "$PAY/apps/native/aurora/launchers"
  find "$REPO_DIR/desktop/aurora" -maxdepth 1 -type f -name '*.desktop' \
    -exec cp -f {} "$PAY/apps/native/aurora/launchers/" \;
fi
python3 - "$PAY/app-catalogs" "$PAY" "$ED" <<'PY'
import json, pathlib, sys
catalog_root, payload, edition = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
files = sorted(str(p.relative_to(catalog_root)) for p in catalog_root.rglob("*") if p.is_file())
manifest = {
    "schema": "aurora-offline-application-bundle-v1",
    "edition": edition,
    "catalog_files": files,
    "native_app_source": "apps/native/aurora",
    "source_snapshot": "repo",
    "policy": "Catalog references are not claims of installation or runtime compatibility. First-party source is bundled; third-party packages remain subject to provider, license, and compatibility checks."
}
(payload / "application-bundle.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("application catalogs:", len(files), "first-party source:", manifest["native_app_source"])
PY

if [ "${ENTRY#desktop/aurora-shell/}" = "$ENTRY" ]; then
  python3 "$HERE/lib/patch_html.py" "$PAY/$ENTRY" "$PAY" wp01.jpg
fi

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

The image boots a Linux kernel. Openbox manages the Aurora kiosk fullscreen state.
Offline application catalogs and first-party application sources are staged under
app-catalogs/ and apps/native/; catalog-only upstream entries are not misrepresented
as installed applications. The native Spit Fire/Koronos kernel remains a separate
release track until its userspace handoff is verified.
EOF

cat > "$PAY/README.txt" <<EOF
$TITLE live image — $VERSION
===============================
Desktop : $ENTRY (fullscreen kiosk)
Keys    : Ctrl+Q quit kiosk · Ctrl+R reload · Ctrl+Alt+F2 text console
Console : login live / live (passwordless sudo)
Menu    : "Classic X session" boots openbox + xterm
Artwork : /opt/aurora/wallpapers and /usr/share/backgrounds/$SHORT
Apps    : /opt/aurora/app-catalogs and /opt/aurora/apps/native
Source  : $REPO_URL
EOF

# ------------------------------------------------------------- system config
log "system configuration"
install -Dm755 "$HERE/lib/aurora-kiosk.py" "$WORK/usr/local/bin/aurora-kiosk.py"

# Linux-style userspace: systemd units, sysusers/tmpfiles, D-Bus policy and helpers.
if [ -d "$REPO_DIR/userspace" ] && [ -f "$REPO_DIR/userspace/Makefile" ]; then
  make -C "$REPO_DIR/userspace" install DESTDIR="$WORK" >/dev/null
  echo "  userspace units installed (aurora-shell.target, jasper/gates/aurora targets)"
fi
install -d "$WORK/etc/aurora"
printf 'AURORA_DESKTOP_URI=file:///opt/aurora/%s\n' "$ENTRY" > "$WORK/etc/aurora/session.conf"
printf '%s\n' "${PROFILE:-aurora}" > "$WORK/etc/aurora/profile"

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
mount_chroot "$WORK"
chroot "$WORK" /bin/bash -c "update-initramfs -u -k all" >/dev/null
umount_chroot "$WORK"

# ------------------------------------------------------------- shrink
# Compile every SDK/toolchain project the host supports; ship the honest report.
if [ -x "$REPO_DIR/tools/build-sdks.sh" ]; then
  log "sdk build"
  mkdir -p "$PAY/reports"
  bash "$REPO_DIR/tools/build-sdks.sh" --out "$PAY/reports/sdk-build-report.json" \
    --max 6 --timeout 120 || true
fi

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
# Wait for an explicit choice: a 5-minute countdown in full menu style, so the
# Jasper/Gates/profile entries are never skipped by an impatient default.
set timeout=300
set timeout_style=menu
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
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Jasper desktop (Windows 12 style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=jasper console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Gates desktop (macOS style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=gates console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Aurora desktop (Linux 7.x style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=aurora console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Classic X session (openbox)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live session=classic console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Safe graphics (nomodeset)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live nomodeset console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Verbose boot" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live console=tty0 console=ttyS0,115200n8
  initrd /live/initrd.img
}
menuentry "Reboot" { reboot }
menuentry "Power off" { halt }
EOF

# Native Koronos kernel: built with the Linux-style kbuild workflow and staged as a
# multiboot2 payload. It is a diagnostic target: the microkernel does not reach a
# verified userspace handoff, so the Linux live entries remain the default.
log "koronos kernel"
if [ -f "$REPO_DIR/kernel/Makefile" ] && command -v nasm >/dev/null 2>&1; then
  ( cd "$REPO_DIR" && make -C kernel defconfig all >/tmp/koronos-build.log 2>&1 ) || \
    echo "  [warn] Koronos build failed, see /tmp/koronos-build.log"
  koronos_elf="$REPO_DIR/build/koronos/x86_64/koronos.elf"
  if [ -s "$koronos_elf" ]; then
    install -Dm644 "$koronos_elf" "$ISODIR/boot/koronos/koronos.elf"
    install -Dm644 "$REPO_DIR/build/koronos/x86_64/System.map" "$ISODIR/boot/koronos/System.map" 2>/dev/null || true
    echo "  staged $(du -h "$koronos_elf" | cut -f1) koronos.elf"
  fi
fi

log "iso"
rm -f "$OUT/$ISO_NAME"
if [ -f "$ISODIR/boot/koronos/koronos.elf" ]; then
  cat >> "$ISODIR/boot/grub/grub.cfg" <<'KORONOS'

menuentry "Koronos native microkernel (diagnostic console — no graphical userspace)" {
  echo "Loading Koronos microkernel (multiboot2)…"
  multiboot2 /boot/koronos/koronos.elf
  boot
}
KORONOS
fi

grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
