#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: docker/iso/entrypoint.sh

Usage:
  docker/iso/entrypoint.sh [options] [arguments]

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
if [[ "${CHIMERA_BUILD:-auto}" == "never" ]]; then
  # Explicit legacy/minimal mode only. It is not the release ISO path.
  if [[ ! -s "$KERNEL_PATH" ]]; then
    echo "error: CHIMERA_BUILD=never but no kernel image exists at $KERNEL_PATH" >&2
    exit 1
  fi
  "$ROOT/tools/build/create-bootable-iso.sh" "$KERNEL_PATH" "$GRUB_CFG" "$OUTPUT_ISO"
else
  # Always prefer the canonical source-first ISO builder in auto/default mode.
  # A stale legacy boot/kernel.bin may exist in the checkout and must not divert
  # release builds into the minimal legacy ISO that omits Koronos/live/recovery.
  echo "Building the canonical full Chimera II OS ISO pipeline (CHIMERA_BUILD=${CHIMERA_BUILD:-auto})."
  "$ROOT/boot/iso/build-iso.sh"
  cp "$ROOT/boot/iso/dist/output.iso" "$OUTPUT_ISO"
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
