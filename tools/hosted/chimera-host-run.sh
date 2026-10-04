#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/hosted/chimera-host-run.sh

Usage:
  tools/hosted/chimera-host-run.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCH="${CHIMERA_GUEST_ARCH:-x86_64}"
MEM="${CHIMERA_VM_MEMORY:-4096}"
CPUS="${CHIMERA_VM_CPUS:-2}"
DISK="${CHIMERA_VM_DISK:-$ROOT/build/hosted/chimera-${ARCH}.qcow2}"
KERNEL="${CHIMERA_KORONOS_ELF:-$ROOT/build/koronos/x86_64/koronos.elf}"
case "$ARCH" in
 x86_64) QEMU="${CHIMERA_QEMU:-qemu-system-x86_64}";; x86) QEMU="${CHIMERA_QEMU:-qemu-system-i386}";; aarch64) QEMU="${CHIMERA_QEMU:-qemu-system-aarch64}";; arm) QEMU="${CHIMERA_QEMU:-qemu-system-arm}";; riscv64) QEMU="${CHIMERA_QEMU:-qemu-system-riscv64}";; *) echo "Unsupported guest architecture: $ARCH" >&2; exit 2;; esac
command -v "$QEMU" >/dev/null 2>&1 || { echo "QEMU not found: $QEMU" >&2; exit 3; }
mkdir -p "$(dirname "$DISK")"
if [[ ! -e "$DISK" ]]; then qemu-img create -f qcow2 "$DISK" "${CHIMERA_VM_DISK_SIZE:-32G}" >/dev/null; fi
args=(-m "$MEM" -smp "$CPUS" -name Chimera-II-OS -drive "file=$DISK,if=virtio,format=qcow2" -nic user)
if [[ -s "$KERNEL" ]]; then args+=(-kernel "$KERNEL"); fi
if [[ "${CHIMERA_VM_GRAPHICS:-1}" == "0" ]]; then args+=(-nographic); fi
if [[ -n "${CHIMERA_VM_ACCEL:-}" ]]; then args+=(-accel "$CHIMERA_VM_ACCEL"); fi
exec "$QEMU" "${args[@]}" "$@"
