#!/usr/bin/env bash
set -euo pipefail

# Create a minimal GRUB bootable ISO containing:
#   /boot/grub/grub.cfg
#   /boot/kernel.bin
#
# Usage:
#   ./tools/build/create-bootable-iso.sh [kernel.bin] [grub.cfg] [output.iso]
#
# Defaults are relative to the repository root:
#   kernel: boot/kernel.bin
#   grub:   boot/iso/grub.cfg
#   output: output.iso

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
KERNEL="${1:-$ROOT/boot/kernel.bin}"
GRUB_CFG="${2:-$ROOT/boot/iso/grub.cfg}"
OUTPUT="${3:-$ROOT/output.iso}"
ISO_ROOT="$ROOT/iso_root"

if [[ ! -f "$KERNEL" ]]; then
  echo "error: compiled kernel not found: $KERNEL" >&2
  echo "Build or copy the kernel as boot/kernel.bin, or pass its path as argument 1." >&2
  exit 1
fi

if [[ ! -f "$GRUB_CFG" ]]; then
  echo "error: GRUB configuration not found: $GRUB_CFG" >&2
  exit 1
fi

if ! command -v grub-mkrescue >/dev/null 2>&1; then
  echo "error: grub-mkrescue is required but was not found." >&2
  echo "Install GRUB rescue/ISO tooling (and xorriso), then retry." >&2
  exit 1
fi

if ! command -v xorriso >/dev/null 2>&1; then
  echo "error: xorriso is required by grub-mkrescue but was not found." >&2
  exit 1
fi

rm -rf "$ISO_ROOT"
mkdir -p "$ISO_ROOT/boot/grub"
cp -- "$GRUB_CFG" "$ISO_ROOT/boot/grub/grub.cfg"
cp -- "$KERNEL" "$ISO_ROOT/boot/kernel.bin"

# Keep the requested layout deterministic and make accidental stale files impossible.
if [[ ! -s "$ISO_ROOT/boot/kernel.bin" ]]; then
  echo "error: staged kernel.bin is empty." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"

echo "Creating bootable ISO..."
echo "  ISO root: $ISO_ROOT"
echo "  GRUB:     $ISO_ROOT/boot/grub/grub.cfg"
echo "  Kernel:   $ISO_ROOT/boot/kernel.bin"
echo "  Output:   $OUTPUT"

grub-mkrescue -o "$OUTPUT" "$ISO_ROOT"

if [[ ! -s "$OUTPUT" ]]; then
  echo "error: grub-mkrescue did not produce a non-empty ISO: $OUTPUT" >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$OUTPUT" | tee "$OUTPUT.sha256"
fi

echo "Bootable ISO created: $OUTPUT"
