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
for cmd in docker cpio grub-mkrescue xorriso mksquashfs mformat mcopy; do have "$cmd" || missing+=("$cmd"); done
(("${#missing[@]}" == 0)) && { echo "All required host build tools are already available."; exit 0; }
printf '[chimera-build-deps] Missing tools: %s\n' "${missing[*]}"
failed=()
try_provider(){
  local manager="$1"; shift
  echo "[chimera-build-deps] Trying $manager for missing host build tools..."
  case "$manager" in
    apt)
      "${SUDO[@]}" apt-get update && "${SUDO[@]}" apt-get install -y docker.io cpio grub-pc-bin grub-efi-amd64-bin xorriso squashfs-tools mtools busybox-static ;;
    dnf|yum)
      "${SUDO[@]}" "$manager" install -y docker cpio grub2-tools-extra grub2-efi-x64-modules xorriso squashfs-tools mtools busybox ;;
    pacman)
      "${SUDO[@]}" pacman -Sy --needed --noconfirm docker cpio grub xorriso squashfs-tools mtools busybox ;;
    zypper)
      "${SUDO[@]}" zypper --non-interactive refresh && "${SUDO[@]}" zypper --non-interactive install docker cpio grub2 xorriso squashfs mtools ;;
    apk)
      "${SUDO[@]}" apk update && "${SUDO[@]}" apk add docker-cli cpio grub xorriso squashfs-tools mtools busybox ;;
    xbps)
      "${SUDO[@]}" xbps-install -Sy docker cpio grub xorriso squashfs-tools mtools busybox ;;
    emerge)
      "${SUDO[@]}" emerge --sync && "${SUDO[@]}" emerge app-containers/docker app-arch/cpio sys-boot/grub app-cdr/xorriso sys-fs/squashfs-tools app-arch/mtools app-misc/busybox ;;
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
    for cmd in docker cpio grub-mkrescue xorriso mksquashfs mformat mcopy; do have "$cmd" || missing+=("$cmd"); done
    (("${#missing[@]}" == 0)) && { echo "[chimera-build-deps] Required tools are now available."; exit 0; }
    printf '[chimera-build-deps] Provider %s returned success but tools remain missing: %s\n' "$manager" "${missing[*]}" >&2
  else
    failed+=("$manager")
    printf '[chimera-build-deps] Provider %s failed; trying another available provider.\n' "$manager" >&2
  fi
done
echo "[chimera-build-deps] Dependency bootstrap failed. Providers attempted: ${failed[*]:-none}; attempted_any=$attempted" >&2
echo "Install Docker, cpio, GRUB rescue tools, xorriso, squashfs-tools and mtools (mformat/mcopy) manually, then retry." >&2
exit 1
