#!/usr/bin/env bash
set -euo pipefail

ROOT=/src
OUTPUT=/output
KERNEL_PATH="${CHIMERA_KERNEL:-$ROOT/boot/kernel.bin}"
GRUB_CFG="${CHIMERA_GRUB_CFG:-$ROOT/boot/iso/grub.cfg}"
OUTPUT_ISO="${CHIMERA_OUTPUT_ISO:-$OUTPUT/output.iso}"

mkdir -p "$OUTPUT"
chmod +x "$ROOT/boot/iso/build-iso.sh" "$ROOT/boot/iso/prepare-layout.sh" "$ROOT/tools/build/create-bootable-iso.sh" "$ROOT/boot/spitfire/build-spitfire.sh"

# The repository build is the full Chimera pipeline: Koronos payload + Spit Fire
# artifacts + GRUB2 + ISO 9660/El Torito. Do not replace it with the minimal
# staging helper, otherwise the source-first ISO structure would be lost.
if [[ "${CHIMERA_BUILD:-auto}" != "never" && ! -f "$KERNEL_PATH" ]]; then
  echo "No boot/kernel.bin found; building the complete Chimera II OS ISO pipeline."
  "$ROOT/boot/iso/build-iso.sh"
  cp "$ROOT/boot/iso/dist/output.iso" "$OUTPUT_ISO"
elif [[ "${CHIMERA_BUILD:-auto}" == "auto" && -f "$KERNEL_PATH" ]]; then
  echo "Using existing boot/kernel.bin with the canonical minimal GRUB ISO generator."
  "$ROOT/tools/build/create-bootable-iso.sh" "$KERNEL_PATH" "$GRUB_CFG" "$OUTPUT_ISO"
elif [[ "${CHIMERA_BUILD:-auto}" == "never" ]]; then
  if [[ ! -f "$KERNEL_PATH" ]]; then
    echo "error: CHIMERA_BUILD=never but no kernel image exists at $KERNEL_PATH" >&2
    exit 1
  fi
  "$ROOT/tools/build/create-bootable-iso.sh" "$KERNEL_PATH" "$GRUB_CFG" "$OUTPUT_ISO"
fi

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

sha256sum "$OUTPUT_ISO" | tee "$OUTPUT_ISO.sha256"
echo "ISO artifact: $OUTPUT_ISO"
