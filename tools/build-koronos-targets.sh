#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-koronos-targets.sh

Usage:
  tools/build-koronos-targets.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/koronos/ports"
mkdir -p "$OUT"

build_port_objects() {
  local name="$1" cc="$2"
  shift 2
  if ! command -v "$cc" >/dev/null 2>&1; then
    printf 'SKIP %-10s compiler %s not installed\n' "$name" "$cc"
    return 0
  fi
  "$cc" -ffreestanding -fno-builtin -fno-stack-protector -nostdinc++ -I"$ROOT/kernel/include" "$@" -c "$ROOT/kernel/core/arch_init.cpp"     -o "$OUT/$name-arch-init.o"
  printf 'BUILT %-10s %s\n' "$name" "$OUT/$name-arch-init.o"
}

build_port_objects aarch64 "${AARCH64_CC:-aarch64-linux-gnu-g++}" -march=armv8-a
build_port_objects riscv64 "${RISCV64_CC:-riscv64-linux-gnu-g++}" -march=rv64gc -mabi=lp64d
