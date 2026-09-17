#!/usr/bin/env bash
set -euo pipefail

ROOT=/src
OUTPUT=/output
KERNEL_PATH="${CHIMERA_KERNEL:-$ROOT/boot/kernel.bin}"
GRUB_CFG="${CHIMERA_GRUB_CFG:-$ROOT/boot/iso/grub.cfg}"
OUTPUT_ISO="${CHIMERA_OUTPUT_ISO:-$OUTPUT/output.iso}"

mkdir -p "$OUTPUT"

if [[ "${CHIMERA_BUILD:-auto}" != "never" && ! -f "$KERNEL_PATH" ]]; then
  echo "No boot/kernel.bin found; building the repository's Multiboot2 bootstrap kernel."
  chmod +x "$ROOT/boot/iso/build-iso.sh" "$ROOT/boot/iso/prepare-layout.sh" "$ROOT/tools/build/create-bootable-iso.sh"
  "$ROOT/boot/iso/build-iso.sh"
  KERNEL_PATH="$ROOT/boot/iso/dist/chimera2os.elf"
fi

if [[ ! -f "$KERNEL_PATH" ]]; then
  echo "error: no kernel image found at $KERNEL_PATH" >&2
  echo "Provide boot/kernel.bin or set CHIMERA_KERNEL to a valid Multiboot2 kernel image." >&2
  exit 1
fi

if [[ ! -f "$GRUB_CFG" ]]; then
  echo "error: GRUB configuration not found: $GRUB_CFG" >&2
  exit 1
fi

"$ROOT/tools/build/create-bootable-iso.sh" "$KERNEL_PATH" "$GRUB_CFG" "$OUTPUT_ISO"

if [[ ! -s "$OUTPUT_ISO" ]]; then
  echo "error: ISO was not produced: $OUTPUT_ISO" >&2
  exit 1
fi

if command -v file >/dev/null 2>&1; then
  file "$OUTPUT_ISO"
fi

if command -v xorriso >/dev/null 2>&1; then
  xorriso -indev "$OUTPUT_ISO" -report_el_torito plain -report_system_area plain -print ''
fi

echo "ISO artifact: $OUTPUT_ISO"
