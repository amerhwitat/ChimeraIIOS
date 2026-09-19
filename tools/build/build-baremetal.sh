#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCH="${CHIMERA_ARCH:-x86_64}"
FIRMWARE="${CHIMERA_FIRMWARE:-uefi}"
BUILD="$ROOT/build/baremetal-$ARCH-$FIRMWARE"
mkdir -p "$ROOT/dist/baremetal"
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=BAREMETAL -DCHIMERA_ARCH="$ARCH" -DCHIMERA_FIRMWARE="$FIRMWARE"
cmake --build "$BUILD" --parallel
printf 'Bare-metal build complete for %s/%s. No device is flashed by this script.\n' "$ARCH" "$FIRMWARE"
