#!/usr/bin/env bash
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
find "$SRC" -type f \( -name LICENSE -o -name COPYING \) -print0 | sort -z | xargs -0 -r sha256sum > "$OUT/LICENSE-SHA256SUMS"
printf "%s\n" "Emulator source build staging complete: $OUT"
