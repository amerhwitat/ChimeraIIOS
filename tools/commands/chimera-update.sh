#!/usr/bin/env bash
set -Eeuo pipefail
usage() {
  cat <<'EOF'
Chimera II OS update manager

Usage:
  chimera-update check   Refresh package metadata and show available updates.
  chimera-update apply   Install available updates (requires root).
  chimera-update --help  Show this help.

No packages are changed by the check command.
EOF
}
case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  check)
    command -v apt-get >/dev/null 2>&1 || { echo "No supported package manager (apt-get) found." >&2; exit 127; }
    if [[ "$(id -u)" -eq 0 ]]; then apt-get update; else sudo apt-get update; fi
    apt list --upgradable 2>/dev/null || true
    ;;
  apply)
    [[ "$(id -u)" -eq 0 ]] || { echo "Run 'sudo chimera-update apply' to install updates." >&2; exit 77; }
    command -v apt-get >/dev/null 2>&1 || { echo "No supported package manager (apt-get) found." >&2; exit 127; }
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
    ;;
  *) usage >&2; exit 2 ;;
esac
