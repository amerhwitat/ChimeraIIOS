#!/usr/bin/env bash
# Install a broad, auditable Linux command-provider set corresponding to the
# SS64 Linux/Bash catalog. Package-by-package installation is intentional:
# unavailable packages and individual apt failures do not abort the
# comprehensive image. In particular, do not use pipefail here: apt-cache
# output can be terminated early by awk and report SIGPIPE (141).
set -u

PACKAGES=(
  coreutils util-linux findutils grep sed gawk mawk diffutils file
  procps psmisc iproute2 iputils-ping net-tools dnsutils traceroute
  openssh-client openssh-server rsync curl wget ca-certificates
  openssl gnupg jq ripgrep fd-find tree less most nano vim-tiny
  bzip2 gzip xz-utils zip unzip zstd tar cpio pax
  acl attr e2fsprogs dos2unix time bc dc
  pciutils usbutils dmidecode lsof strace ltrace
  ethtool iw nftables iptables arping mtr-tiny
  screen tmux ncdu htop iotop sysstat
  rsnapshot logrotate cron at
  p7zip-full rar unrar-free cifs-utils nfs-common
  lvm2 mdadm smartmontools parted gdisk dosfstools exfatprogs
  squashfs-tools xorriso mtools
  shellcheck
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

rm -rf /var/lib/apt/lists/* || true
echo "[Chimera][COMMANDS] Command-provider installation completed."
exit 0
