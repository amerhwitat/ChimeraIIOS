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
# Install Linux command providers and emit an exact package outcome report.
# Default mode preserves best-effort comprehensive builds. Strict mode is used by
# --full and fails if any declared provider package is unavailable or fails.
set -u

STRICT="${CHIMERA_STRICT_COMMAND_PROVIDERS:-0}"
REPORT="${CHIMERA_COMMAND_PROVIDER_REPORT:-/var/log/chimera-command-provider-report.json}"
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
  p7zip-full unrar-free cifs-utils nfs-common
  lvm2 mdadm smartmontools parted gdisk dosfstools exfatprogs
  squashfs-tools xorriso mtools shellcheck dosbox dosbox-x
)

INSTALLED=()
UNAVAILABLE=()
FAILED=()
write_report() {
  mkdir -p "$(dirname "$REPORT")"
  python3 - "$REPORT" "$STRICT" "${INSTALLED[*]}" "${UNAVAILABLE[*]}" "${FAILED[*]}" <<'PY'
import json, pathlib, sys, time
path, strict, installed, unavailable, failed = sys.argv[1:]
doc = {
    "schema": "CHM-COMMAND-PROVIDER-REPORT-1",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "strict": strict == "1",
    "installed": installed.split() if installed else [],
    "unavailable": unavailable.split() if unavailable else [],
    "failed": failed.split() if failed else [],
}
doc["complete"] = not doc["unavailable"] and not doc["failed"]
pathlib.Path(path).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
print(f"[Chimera][COMMANDS] provider report: {path} complete={doc['complete']} installed={len(doc['installed'])} unavailable={len(doc['unavailable'])} failed={len(doc['failed'])}")
PY
}

if ! command -v apt-get >/dev/null 2>&1; then
  echo "[Chimera][COMMANDS][ERROR] apt-get unavailable; no package providers were installed."
  write_report
  [[ "$STRICT" == 1 ]] && exit 1
  exit 0
fi

echo "[Chimera][COMMANDS] Updating apt metadata..."
if ! apt-get update -o Acquire::Retries=5; then
  echo "[Chimera][COMMANDS][ERROR] apt metadata update failed."
  write_report
  [[ "$STRICT" == 1 ]] && exit 1
  exit 0
fi

for pkg in "${PACKAGES[@]}"; do
  candidate=""
  candidate="$(apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2; exit}' 2>/dev/null)" || candidate=""
  if [[ -z "$candidate" || "$candidate" == "(none)" ]]; then
    echo "[Chimera][COMMANDS][WARN] provider unavailable: $pkg"
    UNAVAILABLE+=("$pkg")
    continue
  fi
  if apt-get install -y --no-install-recommends "$pkg"; then
    echo "[Chimera][COMMANDS] installed provider: $pkg"
    INSTALLED+=("$pkg")
  else
    status=$?
    echo "[Chimera][COMMANDS][ERROR] provider failed ($status): $pkg"
    FAILED+=("$pkg")
  fi
done

write_report
rm -rf /var/lib/apt/lists/* || true
if [[ "$STRICT" == 1 && ( ${#UNAVAILABLE[@]} -gt 0 || ${#FAILED[@]} -gt 0 ) ]]; then
  echo "[Chimera][COMMANDS][ERROR] strict provider gate failed; see $REPORT"
  exit 1
fi
echo "[Chimera][COMMANDS] provider installation pass completed."
exit 0
