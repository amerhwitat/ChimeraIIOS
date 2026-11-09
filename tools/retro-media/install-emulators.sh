#!/usr/bin/env bash
set -euo pipefail
if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer currently supports Debian/Ubuntu-derived Chimera and Octavian hosts." >&2
  exit 69
fi
if [ "$(id -u)" -eq 0 ]; then SUDO=; elif command -v sudo >/dev/null 2>&1; then SUDO=sudo; else
  echo "Run as root or install sudo." >&2; exit 77
fi
$SUDO apt-get update
$SUDO apt-get install -y fs-uae vice
command -v fs-uae
command -v x64sc
command -v c1541
fs-uae --version
x64sc --version || true
