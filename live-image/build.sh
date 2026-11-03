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
# grub-efi-amd64-bin mtools dosfstools imagemagick python3 g++ nasm binutils.
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
NATIVE_SOURCE="$REPO_DIR"
if [ "$ED" = "octavian" ]; then NATIVE_SOURCE="$REPO_DIR/vendor/chimera-ii-os/source"; fi
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
if [ ! -f "$BASE/.packages-installed-v2" ]; then
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
      libgl1 libglx-mesa0 libegl1 libgles2 \
      openbox xterm feh mpv \
      geany geany-plugins gnome-builder kdevelop thonny idle lazarus emacs-gtk vim-gtk3 scite bluefish \
      build-essential cmake ninja-build git gdb clang lld pkg-config nasm binutils \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      sudo ca-certificates curl wget less nano htop pciutils usbutils file unzip xz-utils \
      iproute2 iputils-ping netbase procps psmisc rsync \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  touch "$BASE/.packages-installed-v2"
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
    out.append({"name": item["name"], "file": item["file"], "url": item["file"],
                "source": item.get("source", "")})
json.dump(out, open(os.path.join(pay, "wallpapers", "index.json"), "w"), indent=1)
print("wallpapers:", len(out))
PY

# verbatim source snapshot for provenance (excluding build output)
mkdir -p "$PAY/repo"
tar -C "$REPO_DIR" --exclude=./.git --exclude=./live-image/.build -cf - . 2>/dev/null \
  | tar -C "$PAY/repo" -xf - 2>/dev/null || true

# Stage every repository-owned application catalog for offline discovery.
# Catalog-only upstream references remain distinct from installed executables.
mkdir -p "$PAY/app-catalogs" "$PAY/apps/native/aurora"
install -m 0644 "$HERE/ide-catalog.json" "$PAY/app-catalogs/ide-catalog.json"
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

python3 "$HERE/lib/patch_html.py" "$PAY/$ENTRY" "$PAY" wp01.jpg

cat > "$PAY/PROJECT.md" <<EOF
# $TITLE live image payload

- Upstream: $REPO_URL
- Branch: $BRANCH
- Commit: $COMMIT
- Build date: $VERSION (UTC)
- Volume label: $VOLID

`desktop/` is the project's own HTML desktop, rendered fullscreen by the Aurora kiosk
shell (WebKit2GTK). `wallpapers/` holds the artwork shipped with this build, wired into
every page's background picker. `repo/` is a verbatim snapshot of the source tree.

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
install -Dm755 "$HERE/lib/chimera-boot-mode.sh" "$WORK/usr/local/bin/chimera-boot-mode"
install -Dm755 "$HERE/lib/chimera-recovery.sh" "$WORK/usr/local/sbin/chimera-recovery"
if [ -s "$NATIVE_SOURCE/desktop/aurora/assets/Init.mp4" ]; then
  install -D -m 0644 "$NATIVE_SOURCE/desktop/aurora/assets/Init.mp4" "$WORK/usr/share/chimera/aurora/assets/Init.mp4"
  install -D -m 0755 "$NATIVE_SOURCE/desktop/aurora/aurora-init-splash.sh" "$WORK/usr/local/bin/aurora-init-splash.sh"
fi

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

# GTK's fullscreen request is an EWMH message. Without a window manager the
# request is ignored and the undecorated WebView remains at GTK's small default
# size in the upper-left corner in the live session.
if ! command -v openbox >/dev/null 2>&1 || ! command -v xprop >/dev/null 2>&1; then
  echo "[Aurora][FATAL] Openbox and xprop are required for fullscreen desktop mode." >&2
  exit 1
fi
openbox --sm-disable >/tmp/aurora-openbox.log 2>&1 &
wm_pid=$!
wm_ready=0
for attempt in $(seq 1 50); do
  if xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null | grep -Eq 'window id # 0x[[:xdigit:]]+'; then
    wm_ready=1
    break
  fi
  if ! kill -0 "$wm_pid" 2>/dev/null; then
    cat /tmp/aurora-openbox.log >&2 || true
    echo "[Aurora][FATAL] Openbox exited before registering as the window manager." >&2
    exit 1
  fi
  sleep 0.1
done
if [ "$wm_ready" -ne 1 ]; then
  cat /tmp/aurora-openbox.log >&2 || true
  echo "[Aurora][FATAL] Openbox did not become ready; refusing to start a windowed desktop." >&2
  kill "$wm_pid" 2>/dev/null || true
  exit 1
fi
echo "[Aurora] Openbox window manager ready; starting fullscreen desktop."
exec /usr/local/bin/chimera-boot-mode
EOF
python3 - "$WORK/usr/local/bin/aurora-session" "$ENTRY" <<'PY'
from pathlib import Path
import sys
launcher = Path(sys.argv[1])
entry = sys.argv[2]
source = launcher.read_text()
exec_line = "exec /usr/local/bin/chimera-boot-mode"
if source.count(exec_line) != 1:
    raise SystemExit("Aurora session must have exactly one final boot-mode exec")
if "AURORA_DESKTOP_URI=" in source:
    raise SystemExit("Aurora desktop URI must be injected exactly once")
before_exec = (
    'export AURORA_DESKTOP_URI="file:///opt/aurora/' + entry + '"\n'
    'feh --bg-fill /usr/share/backgrounds/aurora-default.jpg 2>/dev/null || true\n'
    'if [[ -x /usr/local/bin/aurora-init-splash.sh && -s /usr/share/chimera/aurora/assets/Init.mp4 ]] && command -v mpv >/dev/null 2>&1; then\n'
    '  CHIMERA_INIT_VIDEO=/usr/share/chimera/aurora/assets/Init.mp4 CHIMERA_SPLASH_MAX_SECONDS=12 /usr/local/bin/aurora-init-splash.sh || echo "[Aurora] Splash failed; continuing."\n'
    'fi\n'
)
source = source.replace(exec_line, before_exec + exec_line, 1)
launcher.write_text(source)
PY
test -s "$PAY/$ENTRY"
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
install -D -m 0644 "$PAY/wallpapers/wp01.jpg" "$WORK/usr/share/backgrounds/aurora-default.jpg"

printf 'MODULES=most\nCOMPRESS=gzip\n' > "$WORK/etc/initramfs-tools/conf.d/live.conf"
mount_chroot "$WORK"
chroot "$WORK" /bin/bash -c "update-initramfs -u -k all" >/dev/null
umount_chroot "$WORK"

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

# Build the repository's native Koronos kernel by default. An externally
# built ELF may be supplied explicitly, but it must satisfy the same checks.
if [[ -z "${KORONOS_ELF:-}" ]]; then
  if [[ -f "$REPO_DIR/kernel/build-koronos.sh" ]]; then
    KERNEL_ROOT="$REPO_DIR"
  elif [[ -f "$REPO_DIR/vendor/chimera-ii-os/source/kernel/build-koronos.sh" ]]; then
    KERNEL_ROOT="$REPO_DIR/vendor/chimera-ii-os/source"
  else
    echo "ERROR: native Koronos source/build script is missing; refusing to emit a misleading Koronos boot entry." >&2
    exit 1
  fi
  log "building native Koronos kernel from $KERNEL_ROOT"
  bash "$KERNEL_ROOT/kernel/build-koronos.sh"
  KORONOS_ELF="$KERNEL_ROOT/build/koronos/x86_64/koronos.elf"
fi
KORONOS_ELF="$(realpath "$KORONOS_ELF")"
test -s "$KORONOS_ELF" || { echo "ERROR: Koronos ELF missing: $KORONOS_ELF" >&2; exit 1; }

# Embed only a validated Multiboot2-compatible x86-64 Koronos kernel.
if [[ -n "${KORONOS_ELF:-}" ]]; then
  test -s "$KORONOS_ELF" || { echo "KORONOS_ELF is set but the file is missing/empty" >&2; exit 1; }
  python3 - "$KORONOS_ELF" <<'PY'
import pathlib, struct, sys
p = pathlib.Path(sys.argv[1])
d = p.read_bytes()
if len(d) < 64 or d[:4] != b'\x7fELF' or d[4] != 2 or d[5] != 1:
    raise SystemExit("Koronos artifact must be a little-endian ELF64 image")
if struct.unpack_from("<H", d, 18)[0] != 62:
    raise SystemExit("Koronos artifact must target x86-64 (EM_X86_64)")
magic = 0xE85250D6
valid = False
for off in range(0, min(len(d), 32768) - 16, 8):
    if struct.unpack_from("<I", d, off)[0] != magic:
        continue
    arch, length, checksum = struct.unpack_from("<III", d, off + 4)
    if arch == 0 and length >= 16 and off + length <= len(d) and ((magic + arch + length + checksum) & 0xffffffff) == 0:
        valid = True
        break
if not valid:
    raise SystemExit("Koronos ELF has no valid Multiboot2 header in its first 32 KiB")
print("Validated Multiboot2 x86-64 Koronos ELF:", p)
PY
  install -Dm644 "$KORONOS_ELF" "$ISODIR/boot/koronos.elf"
fi
# Build and stage the native Spit Fire BIOS artifacts. GRUB2 remains the
# El Torito/UEFI ISO loader; these MBR artifacts are not written to ISO boot sectors.
SPITFIRE_OUT="$BUILD/spitfire"
mkdir -p "$SPITFIRE_OUT" "$ISODIR/boot/spitfire" "$ISODIR/boot/jasper"
for tool in nasm g++ ld nm; do command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: Spit Fire build requires $tool" >&2; exit 2; }; done
bash "$NATIVE_SOURCE/boot/spitfire/build-spitfire.sh" "$SPITFIRE_OUT" "$KORONOS_ELF"
for artifact in spitfire-sf0-mbr.bin spitfire-stage2.bin spitfire-sf1-longmode.o spitfire-sf2-loader.o BUILD-MANIFEST.txt SHA256SUMS; do
  test -s "$SPITFIRE_OUT/$artifact" || { echo "ERROR: missing Spit Fire artifact $artifact" >&2; exit 2; }
  install -m 0644 "$SPITFIRE_OUT/$artifact" "$ISODIR/boot/spitfire/$artifact"
done
install -m 0644 "$NATIVE_SOURCE/boot/spitfire/spitfire-menu.cfg" "$ISODIR/boot/spitfire/native-koronos-menu.cfg"
install -m 0644 "$HERE/spitfire-menu.cfg" "$ISODIR/boot/spitfire/spitfire-menu.cfg"
install -m 0644 "$HERE/jasper-live.cfg" "$ISODIR/boot/jasper/live-image.cfg"
install -D -m 0644 "$PAY/wallpapers/wp01.jpg" "$ISODIR/boot/grub/background.jpg"
# Build separate native Koronos Installer and Recovery initramfs candidates.
# They are deliberately staged outside the active boot paths: the current
# native CPL3/userspace acceptance gate has not certified these runtimes.
CANDIDATE_ROOT="$BUILD/native-runtime-candidates"
mkdir -p "$CANDIDATE_ROOT/installer-stage" "$ISODIR/boot/candidates/installer" "$ISODIR/boot/candidates/recovery"
CHIMERA_BUILD_DIR="$NATIVE_SOURCE/build" CHIMERA_KORONOS_KERNEL="$KORONOS_ELF" \
  bash "$NATIVE_SOURCE/tools/build-live-boot-binaries.sh"
bash "$NATIVE_SOURCE/tools/chimera-stage-installer-media.sh" "$CANDIDATE_ROOT/installer-stage"
for artifact in installation.img installer-initrd.img installation-manifest.json installer-contract.json installation_phases.json installer_profiles.json; do
  src="$CANDIDATE_ROOT/installer-stage/install/installer/$artifact"
  if [ -s "$src" ]; then install -m 0644 "$src" "$ISODIR/boot/candidates/installer/$artifact"; fi
done
RECOVERY_CANDIDATE="$NATIVE_SOURCE/build/live-boot/boot/recovery"
for artifact in chimera-recovery-initramfs.img chimera-recovery-initramfs.img.sha256 recovery-manifest.json; do
  if [ -s "$RECOVERY_CANDIDATE/$artifact" ]; then install -m 0644 "$RECOVERY_CANDIDATE/$artifact" "$ISODIR/boot/candidates/recovery/$artifact"; fi
done
python3 - "$ISODIR/boot/candidates" "$ED" <<'PY'
import hashlib, json, pathlib, sys
root, edition = pathlib.Path(sys.argv[1]), sys.argv[2]
def files(path):
    out=[]
    for p in sorted(path.rglob("*")):
        if p.is_file():
            out.append({"path":str(p.relative_to(root)),"size":p.stat().st_size,
                        "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    return out
manifest={
 "schema":"koronos-native-runtime-candidates-v1",
 "edition":edition,
 "installer":{"artifacts":files(root/"installer"),"bootable":False},
 "recovery":{"artifacts":files(root/"recovery"),"bootable":False},
 "activation_policy":"Candidate images are not copied to the active GRUB/Koronos handoff paths. Native installer/recovery remain blocked until the CPL3 syscall/PID readiness and target-specific cold-boot verifiers pass.",
 "status":"built-candidate-not-production-runtime"
}
(root/"native-runtime-candidates.json").write_text(json.dumps(manifest,indent=2)+"\\n")
PY



cat > "$ISODIR/boot/grub/grub.cfg" <<EOF
set default=0
set timeout=8
insmod all_video
insmod gfxterm
insmod png
insmod jpeg
insmod font
set gfxmode=5120x2880,3840x2160,2560x1440,1920x1200,1920x1080,1680x1050,1600x1200,1600x900,1440x900,1366x768,1280x1024,1280x720,1024x768,800x600,640x480,auto
set gfxpayload=keep
set debug=all
terminal_output gfxterm
if [ -f /boot/grub/background.jpg ]; then background_image --mode stretch /boot/grub/background.jpg; fi
echo "[SPIT FIRE] $TITLE $VERSION — firmware handoff"
echo "[SPIT FIRE] Next: Jasper / GRUB 2 target manager"
configfile /boot/spitfire/spitfire-menu.cfg
EOF

log "iso"
rm -f "$OUT/$ISO_NAME"
grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
