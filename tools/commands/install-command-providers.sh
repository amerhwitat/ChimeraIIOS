#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/commands/install-command-providers.sh

Usage:
  tools/commands/install-command-providers.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
# Install a broad, auditable Linux command-provider set corresponding to the
# SS64 Linux/Bash catalog. Package-by-package installation is intentional:
# unavailable packages and individual apt failures do not abort the
# comprehensive image. In particular, do not use pipefail here: apt-cache
# output can be terminated early by awk and report SIGPIPE (141).
set -u

PACKAGES=(
  coreutils util-linux findutils grep sed gawk mawk diffutils file busybox-static
  # Verified upstream command providers (where available in this Debian rootfs).
  chkconfig inetutils-ftp krb5-user lprng plocate rsh-client fdutils ntpsec
  # Open-source interactive shells from the Aurora Shells registry.
  bash zsh fish dash mksh yash elvish nushell
  # Open-source terminal emulators from the Aurora Terminals registry.
  alacritty blackbox-terminal contour foot ghostty gnome-console gnome-terminal kitty
  konsole lxterminal mate-terminal ptyxis qterminal sakura terminator terminology tilix
  wezterm xfce4-terminal xterm
  procps psmisc kmod systemd-resolved iproute2 iputils-ping net-tools dnsutils traceroute
  openssh-client openssh-server rsync curl wget ca-certificates
  openssl gnupg jq ripgrep fd-find tree less most nano vim-tiny
  bzip2 gzip xz-utils zip unzip zstd tar cpio pax
  acl attr e2fsprogs dos2unix time bc dc
  pciutils usbutils dmidecode lsof strace ltrace bubblewrap python3-tk
  ethtool iw nftables iptables arping mtr-tiny
  screen tmux ncdu htop iotop sysstat
  rsnapshot logrotate cron at
  p7zip-full unrar-free cifs-utils nfs-common
  lvm2 mdadm smartmontools parted gdisk dosfstools exfatprogs
  btrfs-progs cryptsetup tcpdump redis-tools zfsutils-linux
  squashfs-tools xorriso mtools
  shellcheck dosbox dosbox-x qemu-user-static
  # Optional cross-platform compatibility runtimes; absent packages remain explicit in coverage.
  wine wine64 powershell mono-runtime dotnet-runtime-8.0
  wasmtime wasmer darling
  rpm dnf zypper flatpak snapd pacman-package-manager
  build-essential clang cmake ninja-build python3 python3-pip python3-venv python-is-python3
  apache2 auditd fwupd fprintd policykit-1 realmd wayland-utils qemu-system-x86 podman
  kubernetes-client packagekit-tools grub2-common passwd nasm
  nodejs npm default-jdk golang-go rustc cargo php-cli ruby sqlite3
  postgresql-client mariadb-client
)

if ! command -v apt-get >/dev/null 2>&1; then
  echo "[Chimera][COMMANDS] apt-get unavailable; command-provider install skipped."
  exit 0
fi

echo "[Chimera][COMMANDS] Updating apt metadata..."
if ! apt-get update -o Acquire::Retries=5; then
  echo "[Chimera][COMMANDS][WARN] apt metadata update failed; skipping command-provider installation."
  exit 0
fi

for pkg in "${PACKAGES[@]}"; do
  # Keep this lookup non-fatal. Some apt-cache/awk combinations can return
  # 141 (SIGPIPE) when the consumer exits after the first Candidate line.
  candidate=""
  candidate="$(apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2; exit}' 2>/dev/null)" || candidate=""

  if [[ -z "$candidate" || "$candidate" == "(none)" ]]; then
    echo "[Chimera][COMMANDS] unavailable: $pkg"
    continue
  fi

  if apt-get install -y --no-install-recommends "$pkg"; then
    echo "[Chimera][COMMANDS] installed provider: $pkg"
  else
    status=$?
    echo "[Chimera][COMMANDS][WARN] provider failed ($status): $pkg"
    # Continue with the remaining providers; one package must never make the
    # comprehensive image fail.
  fi
done

# MongoDB's official Debian 13 repository supplies the real mongosh CLI.
# Only the signed MongoDB repository is added; no database server is installed.
arch="$(dpkg --print-architecture 2>/dev/null || true)"
if [[ "$arch" == "amd64" || "$arch" == "arm64" ]] && command -v curl >/dev/null 2>&1 && command -v gpg >/dev/null 2>&1; then
  key_tmp="$(mktemp)"
  keyring="/usr/share/keyrings/mongodb-enterprise-9.0.gpg"
  if curl -fsSL https://pgp.mongodb.com/server-9.0.asc -o "$key_tmp" &&
     gpg --dearmor --yes -o "$keyring" "$key_tmp"; then
    printf 'deb [arch=%s signed-by=%s] https://repo.mongodb.com/apt/debian trixie/mongodb-enterprise/9.0 main\n' "$arch" "$keyring" \
      > /etc/apt/sources.list.d/mongodb-enterprise-9.0.list
    if apt-get update -o Acquire::Retries=5 &&
       apt-get install -y --no-install-recommends mongodb-mongosh &&
       command -v mongosh >/dev/null 2>&1 && mongosh --version; then
      echo "[Chimera][COMMANDS] installed verified official MongoDB mongosh provider"
    else
      echo "[Chimera][COMMANDS][WARN] official mongosh package unavailable; strict provider gate will report it"
    fi
  else
    echo "[Chimera][COMMANDS][WARN] MongoDB signing key could not be verified; mongosh was not installed"
  fi
  rm -f "$key_tmp"
else
  echo "[Chimera][COMMANDS][WARN] mongosh repository unsupported for this target architecture"
fi

# Install the official OpenShift CLI from a version-pinned release archive.
# SHA-256 values are pinned per architecture; no unverified "latest" binary is used.
oc_arch="$(dpkg --print-architecture 2>/dev/null || true)"
oc_version="5.0.1"
case "$oc_arch" in
  amd64)
    oc_url="https://mirror.openshift.com/pub/openshift-v4/clients/ocp/$oc_version/openshift-client-linux.tar.gz"
    oc_sha="9be0ad418ece7aa19fbb99a9259a800c4d234d08766c9b782eb321659b9c59e8"
    ;;
  arm64)
    oc_url="https://mirror.openshift.com/pub/openshift-v4/clients/ocp/$oc_version/openshift-client-linux-arm64.tar.gz"
    oc_sha="77a0e93ef62716fcf057a5d336a7f715c066013df792241489df7b0da18a92f4"
    ;;
  *) oc_url=""; oc_sha="" ;;
esac
if [[ -n "$oc_url" ]] && command -v curl >/dev/null 2>&1 && command -v sha256sum >/dev/null 2>&1; then
  oc_tmp="$(mktemp -d)"
  if curl -fsSL "$oc_url" -o "$oc_tmp/openshift-client.tar.gz" &&
     printf '%s  %s\n' "$oc_sha" "$oc_tmp/openshift-client.tar.gz" | sha256sum --check --status &&
     tar -xzf "$oc_tmp/openshift-client.tar.gz" -C "$oc_tmp" oc kubectl &&
     install -D -m 0755 "$oc_tmp/oc" /usr/bin/oc &&
     install -D -m 0755 "$oc_tmp/kubectl" /usr/bin/kubectl &&
     /usr/bin/oc version --client >/dev/null 2>&1 &&
     /usr/bin/kubectl version --client --output=json >/dev/null 2>&1; then
    echo "[Chimera][COMMANDS] installed verified OpenShift oc $oc_version for $oc_arch"
  else
    echo "[Chimera][COMMANDS][WARN] pinned OpenShift client failed download/checksum/runtime verification"
  fi
  rm -rf "$oc_tmp"
else
  echo "[Chimera][COMMANDS][WARN] OpenShift client not published for target architecture $oc_arch"
fi

rm -rf /var/lib/apt/lists/* || true
echo "[Chimera][COMMANDS] Command-provider installation completed."
exit 0
