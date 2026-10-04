#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/installer/chimera-installer.sh

Usage:
  tools/installer/chimera-installer.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE="interactive"
DRY_RUN=1

usage() {
  cat <<'EOF'
Chimera II OS installer planner

Usage: chimera-installer.sh [--profile PROFILE] [--execute]

Profiles: interactive workstation server developer minimal
Default mode is dry-run and never partitions, formats, mounts, installs a bootloader,
or replaces drivers.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2;;
    --execute) DRY_RUN=0; shift;;
    -h|--help) usage; exit 0;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2;;
  esac
done

python3 "$ROOT/tools/installer/installer_plan.py" \
  --target linux --profile "$PROFILE" \
  $( [[ "$DRY_RUN" -eq 0 ]] && printf '%s' '--execute' )

cat <<'EOF'

Next stages are adapter-controlled:
  1. Inventory UEFI/ACPI/PCI/USB/network/GPU/storage.
  2. Resolve driver + firmware candidates and license status.
  3. Present GPT/LVM/RAID/filesystem layout before any write.
  4. Require an explicit destructive confirmation token.
  5. Install Chimera II boot files and base system.
  6. Enable optional Aurora/Wayland and service profiles.
  7. Reboot only after a bootability validation pass.
EOF
