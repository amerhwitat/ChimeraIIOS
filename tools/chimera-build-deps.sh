#!/usr/bin/env bash
# Optional, explicit host dependency bootstrap with provider fallback.
set -Eeuo pipefail
if [[ "${CHIMERA_INSTALL_BUILD_DEPS:-0}" != 1 ]]; then
  echo "Build dependency auto-install is disabled. Set CHIMERA_INSTALL_BUILD_DEPS=1 to opt in." >&2
  exit 2
fi
if (( EUID == 0 )); then SUDO=(); elif command -v sudo >/dev/null 2>&1; then SUDO=(sudo); else
  echo "Installing build dependencies requires root or sudo." >&2; exit 2
fi
have(){ command -v "$1" >/dev/null 2>&1; }
missing=()
for cmd in docker cpio grub-mkrescue xorriso mksquashfs git make gcc g++ cmake ninja cargo rustc go autoconf autoreconf readelf meson pkg-config python3; do have "$cmd" || missing+=("$cmd"); done
(("${#missing[@]}" == 0)) && { echo "All required host build tools are already available."; exit 0; }
printf '[chimera-build-deps] Missing tools: %s\n' "${missing[*]}"
failed=()
try_provider(){
  local manager="$1"; shift
  echo "[chimera-build-deps] Trying $manager for missing host build tools..."
  case "$manager" in
    apt)
      "${SUDO[@]}" apt-get update && "${SUDO[@]}" apt-get install -y docker.io cpio grub-pc-bin grub-efi-amd64-bin xorriso squashfs-tools busybox-static git build-essential cmake ninja-build cargo rustc golang-go autoconf automake libtool binutils meson pkg-config python3 python3-venv python3-pip libssl-dev zlib1g-dev libffi-dev libreadline-dev libsqlite3-dev libncurses-dev libboost-dev libgtk-3-dev libgtk-4-dev libadwaita-1-dev libvte-2.91-dev libvte-2.91-gtk4-dev libwayland-dev libxkbcommon-dev libxkbcommon-x11-dev libx11-dev libxcb1-dev libegl1-mesa-dev libgl1-mesa-dev libvulkan-dev libfontconfig1-dev libfreetype6-dev libharfbuzz-dev libyaml-cpp-dev libutf8proc-dev libpcre2-dev libicu-dev libcairo2-dev libpango1.0-dev libepoxy-dev libpixman-1-dev libdbus-1-dev libsystemd-dev libudev-dev librsvg2-bin nasm ;;
    dnf|yum)
      "${SUDO[@]}" "$manager" install -y docker cpio grub2-tools-extra grub2-efi-x64-modules xorriso squashfs-tools busybox ;;
    pacman)
      "${SUDO[@]}" pacman -Sy --needed --noconfirm docker cpio grub xorriso squashfs-tools busybox git base-devel cmake ninja cargo rust go autoconf automake libtool binutils meson pkgconf python python-pip ;;
    zypper)
      "${SUDO[@]}" zypper --non-interactive refresh && "${SUDO[@]}" zypper --non-interactive install docker cpio grub2 xorriso squashfs git make gcc gcc-c++ cmake ninja cargo rust go autoconf automake libtool binutils meson pkg-config python3 python3-pip ;;
    apk)
      "${SUDO[@]}" apk update && "${SUDO[@]}" apk add docker-cli cpio grub xorriso squashfs-tools busybox git build-base cmake ninja cargo rust go autoconf automake libtool binutils meson pkgconf python3 py3-pip ;;
    xbps)
      "${SUDO[@]}" xbps-install -Sy docker cpio grub xorriso squashfs-tools busybox git base-devel cmake ninja cargo rust go autoconf automake libtool binutils meson pkg-config python3 python3-pip ;;
    emerge)
      "${SUDO[@]}" emerge --sync && "${SUDO[@]}" emerge app-containers/docker app-arch/cpio sys-boot/grub app-cdr/xorriso sys-fs/squashfs-tools app-misc/busybox dev-vcs/git sys-devel/gcc sys-devel/make dev-build/cmake dev-build/ninja dev-lang/rust dev-lang/go sys-devel/autoconf sys-devel/automake dev-build/libtool dev-util/pkgconf dev-build/meson dev-lang/python app-arch/binutils ;;
    *) return 2 ;;
  esac
}
attempted=0
for manager in apt dnf yum pacman zypper apk xbps-install emerge; do
  case "$manager" in
    apt) have apt-get || continue ;;
    dnf|yum|pacman|zypper|apk|emerge) have "$manager" || continue ;;
    xbps-install) have xbps-install || continue; manager=xbps ;;
  esac
  attempted=1
  if try_provider "$manager"; then
    missing=()
    for cmd in docker cpio grub-mkrescue xorriso mksquashfs git make gcc g++ cmake ninja cargo rustc go autoconf autoreconf readelf meson pkg-config python3; do have "$cmd" || missing+=("$cmd"); done
    (("${#missing[@]}" == 0)) && { echo "[chimera-build-deps] Required tools are now available."; exit 0; }
    printf '[chimera-build-deps] Provider %s returned success but tools remain missing: %s\n' "$manager" "${missing[*]}" >&2
  else
    failed+=("$manager")
    printf '[chimera-build-deps] Provider %s failed; trying another available provider.\n' "$manager" >&2
  fi
done
echo "[chimera-build-deps] Dependency bootstrap failed. Providers attempted: ${failed[*]:-none}; attempted_any=$attempted" >&2
echo "Install Docker, cpio, GRUB rescue tools, xorriso, squashfs-tools, Git, C/C++/Rust/Go toolchains, CMake/Ninja/Meson, Autoconf and Python tooling manually, then retry." >&2
exit 1
