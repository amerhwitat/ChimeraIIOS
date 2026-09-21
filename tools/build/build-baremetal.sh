#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCH="${CHIMERA_ARCH:-x86_64}"
FIRMWARE="${CHIMERA_FIRMWARE:-uefi}"
BUILD="$ROOT/build/baremetal-$ARCH-$FIRMWARE"
mkdir -p "$ROOT/dist/baremetal"
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=BAREMETAL -DCHIMERA_ARCH="$ARCH" -DCHIMERA_FIRMWARE="$FIRMWARE"
cmake --build "$BUILD" --parallel
printf 'Bare-metal build complete for %s/%s. No device is flashed by this script.\n' "$ARCH" "$FIRMWARE"
