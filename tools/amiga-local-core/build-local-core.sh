#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${ROOT}/.local/amiga-core"
SRC="${OUT}/libretro-uae"
mkdir -p "${OUT}"
if [ ! -d "${SRC}/.git" ]; then
  git clone --depth 1 https://github.com/libretro/libretro-uae.git "${SRC}"
else
  git -C "${SRC}" pull --ff-only
fi
make -C "${SRC}" -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
CORE="$(find "${SRC}" -maxdepth 3 -type f -name '*_libretro.so' -print -quit)"
if [ -z "${CORE}" ]; then
  echo "PUAE core build completed but no *_libretro.so was found." >&2
  exit 1
fi
mkdir -p "${OUT}/cores"
cp "${CORE}" "${OUT}/cores/puae_libretro.so"
printf 'Local Amiga core: %s\n' "${OUT}/cores/puae_libretro.so"
printf 'Pages packaging: DISABLED / local-only\n'
