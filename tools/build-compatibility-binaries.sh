#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FOREIGN="$ROOT/build/foreign"
SRC="$FOREIGN/source"
BIN="$FOREIGN/binaries"
mkdir -p "$BIN/windows" "$BIN/macos"

build_wine() {
  local src="$SRC/Wine"
  [[ -d "$src" ]] || return 0
  command -v make >/dev/null || return 0
  command -v gcc >/dev/null || return 0
  (cd "$src" && ./configure --prefix="$BIN/windows/wine" --disable-tests >/dev/null 2>&1 && make -j"${CHIMERA_JOBS:-2}" && make install) || echo "Wine build skipped/failed; source retained."
}

build_darling() {
  local src="$SRC/Darling"
  [[ -d "$src" ]] || return 0
  command -v cmake >/dev/null || return 0
  mkdir -p "$src/build"
  (cd "$src/build" && cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1 && cmake --build . -j"${CHIMERA_JOBS:-2}") || echo "Darling build skipped/failed; source retained."
  [[ -d "$src/build" ]] && cp -a "$src/build/." "$BIN/macos/darling-build/" 2>/dev/null || true
}

build_wine
build_darling
find "$BIN" -type f -exec sha256sum {} + > "$FOREIGN/metadata/compatibility-binaries.SHA256SUMS" 2>/dev/null || true
