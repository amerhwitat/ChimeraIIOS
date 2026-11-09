#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/retro-emulators"
JOBS="${JOBS:-2}"
while (($#)); do case "$1" in --out) OUT="$(mkdir -p "$2" && cd "$2" && pwd)"; shift 2;; --jobs) JOBS="$2"; shift 2;; -h|--help) echo "Usage: $0 [--out DIR] [--jobs N]"; exit 0;; *) echo "Unknown option: $1" >&2; exit 64;; esac; done
for tool in git make gcc g++ pkg-config autoconf automake libtoolize; do command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 127; }; done
mkdir -p "$OUT" "$OUT/licenses"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
PUAE_SHA=d366f77c60e5a5f059f129cc3773d3048306083b
VICE_SHA=635853a38f93e2d5da8d0c9ea42a30ad60f52fe6
git clone --filter=blob:none --no-checkout https://github.com/libretro/libretro-uae.git "$TMP/libretro-uae"
git -C "$TMP/libretro-uae" checkout --detach "$PUAE_SHA"
make -C "$TMP/libretro-uae" -j"$JOBS"
PUAE="$TMP/libretro-uae/puae_libretro.so"; test -s "$PUAE"
install -m 0644 "$PUAE" "$OUT/puae_libretro.so"
git clone --filter=blob:none --no-checkout https://github.com/VICE-Team/svn-mirror.git "$TMP/vice"
git -C "$TMP/vice" checkout --detach "$VICE_SHA"
cd "$TMP/vice/vice"
./autogen.sh
./configure --enable-sdl2ui --without-alsa --without-pulse
make -j"$JOBS"
for name in x64sc x64 c1541; do
 candidate="$TMP/vice/vice/src/$name"
 test -s "$candidate" || { echo "VICE build did not produce $name" >&2; exit 1; }
 install -m 0755 "$candidate" "$OUT/$name"
done
cp "$TMP/libretro-uae/COPYING" "$OUT/licenses/PUAE-COPYING" 2>/dev/null || true
cp "$TMP/vice/vice/COPYING" "$OUT/licenses/VICE-COPYING" 2>/dev/null || true
file "$OUT/puae_libretro.so" "$OUT/x64sc" "$OUT/x64" "$OUT/c1541" > "$OUT/binary-types.txt"
readelf -h "$OUT/puae_libretro.so" | grep -Eq 'Type:[[:space:]]+DYN'
readelf -h "$OUT/x64sc" | grep -Eq 'Type:[[:space:]]+EXEC'
readelf -h "$OUT/c1541" | grep -Eq 'Type:[[:space:]]+EXEC'
ldd "$OUT/x64sc" > "$OUT/x64sc-dependencies.txt"
ldd "$OUT/c1541" > "$OUT/c1541-dependencies.txt"
(cd "$OUT" && sha256sum puae_libretro.so x64sc x64 c1541 > SHA256SUMS)
echo "Built and inspected PUAE and VICE providers in $OUT"
