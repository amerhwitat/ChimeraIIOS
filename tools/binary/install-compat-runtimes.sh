#!/usr/bin/env bash
set -euo pipefail
if ! command -v apt-get >/dev/null 2>&1; then
  echo "This bootstrap currently supports Debian/Ubuntu-derived hosts." >&2
  exit 69
fi
if [ "$(id -u)" -eq 0 ]; then SUDO=; elif command -v sudo >/dev/null 2>&1; then SUDO=sudo; else
  echo "Run as root or install sudo." >&2; exit 77
fi
$SUDO apt-get update
$SUDO apt-get install -y qemu-user qemu-user-static wine64 dosbox
for tool in qemu-aarch64 qemu-arm qemu-riscv64 qemu-riscv32 wine dosbox; do
  if command -v "$tool" >/dev/null 2>&1; then printf 'available: %s\n' "$tool"; else printf 'not-found: %s\n' "$tool"; fi
done
