#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-emulator-stack.sh

Usage:
  tools/build-emulator-stack.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CHIMERA_EMULATOR_SRC:-$ROOT/build/emulator-src}"
OUT="${CHIMERA_EMULATOR_OUT:-$ROOT/build/emulators}"
mkdir -p "$SRC" "$OUT"
clone_build() {
  local name="$1" url="$2" ref="$3" cmd="$4" dir="$SRC/$1"
  [[ -d "$dir/.git" ]] || git clone --filter=blob:none "$url" "$dir"
  git -C "$dir" fetch --depth 1 origin "$ref" || true
  git -C "$dir" checkout "$ref"
  bash -lc "cd \"$dir\" && $cmd"
}
[[ "${CHIMERA_BUILD_RETROARCH:-0}" == 1 ]] && clone_build retroarch https://github.com/libretro/RetroArch.git "${CHIMERA_RETROARCH_REV:-master}" "make -j$(nproc)"
[[ "${CHIMERA_BUILD_MAME:-0}" == 1 ]] && clone_build mame https://github.com/mamedev/mame.git "${CHIMERA_MAME_REV:-master}" "make -j$(nproc) REGENIE=1"
[[ "${CHIMERA_BUILD_DOSBOX:-0}" == 1 ]] && clone_build dosbox https://github.com/dosbox-staging/dosbox-staging.git "${CHIMERA_DOSBOX_REV:-master}" "meson setup build --buildtype=release && meson compile -C build"
[[ "${CHIMERA_BUILD_SCUMMVM:-0}" == 1 ]] && clone_build scummvm https://github.com/scummvm/scummvm.git "${CHIMERA_SCUMMVM_REV:-master}" "make -j$(nproc)"
[[ "${CHIMERA_BUILD_PCSX_REDUX:-0}" == 1 ]] && clone_build pcsx-redux https://github.com/grumpycoders/pcsx-redux.git "${CHIMERA_PCSX_REDUX_REV:-main}" "make -j$(nproc)"
[[ "${CHIMERA_BUILD_PCSX2:-0}" == 1 ]] && clone_build pcsx2 https://github.com/PCSX2/pcsx2.git "${CHIMERA_PCSX2_REV:-master}" "cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)"
[[ "${CHIMERA_BUILD_RPCS3:-0}" == 1 ]] && clone_build rpcs3 https://github.com/RPCS3/rpcs3.git "${CHIMERA_RPCS3_REV:-master}" "cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)"
[[ "${CHIMERA_BUILD_SHADPS4:-0}" == 1 ]] && clone_build shadps4 https://github.com/shadps4-emu/shadPS4.git "${CHIMERA_SHADPS4_REV:-main}" "cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)"
find "$SRC" -type f \( -name LICENSE -o -name COPYING \) -print0 | sort -z | xargs -0 -r sha256sum > "$OUT/LICENSE-SHA256SUMS"
if [[ "${CHIMERA_COMPRESS_EMULATORS:-1}" == 1 ]]; then
  mkdir -p "$OUT/payloads"
  find "$OUT" -type f -perm -111 -not -path "*/payloads/*" -print0 | while IFS= read -r -d "" bin; do
    if command -v zstd >/dev/null 2>&1; then zstd -q -f -19 "$bin" -o "$OUT/payloads/$(basename "$bin").zst"; fi
  done
fi
printf "%s\n" "Emulator source build staging complete: $OUT"
