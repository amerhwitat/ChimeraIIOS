#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: build-terminal-shell-sources.sh ROOTFS SOURCE_BUILD_DIR}"
OUT="${2:?usage: build-terminal-shell-sources.sh ROOTFS SOURCE_BUILD_DIR}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MISSING="$ROOTFS/usr/share/chimera/aurora/terminal-shell-source-required.tsv"
INSTALLED="$ROOTFS/usr/share/chimera/aurora/terminal-shell-installed.tsv"
[[ -s "$MISSING" ]] || { echo "No source-build-required terminal/shell providers."; exit 0; }
mkdir -p "$OUT/src" "$OUT/stage/usr/local/bin"
require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing source-build dependency: $1" >&2; exit 2; }; }
TARGET_ARCH="${CHIMERA_TARGET_ARCH:-$(uname -m)}"
verify_target_elf() {
  local binary="$1" machine expected
  require readelf
  case "$TARGET_ARCH" in
    x86_64|amd64) expected="Advanced Micro Devices X86-64" ;;
    aarch64|arm64) expected="AArch64" ;;
    armv7|armv7l|armhf) expected="ARM" ;;
    riscv64) expected="RISC-V" ;;
    i686|i386) expected="Intel 80386" ;;
    *) echo "Unsupported CHIMERA_TARGET_ARCH=$TARGET_ARCH; refusing unverified provider" >&2; exit 2 ;;
  esac
  machine="$(readelf -h "$binary" | awk -F: '/^[[:space:]]*Machine:/ {sub(/^[[:space:]]+/, "", $2); print $2}')"
  [[ -n "$machine" && "$machine" == *"$expected"* ]] || {
    echo "Provider architecture mismatch: $binary target=$TARGET_ARCH ELF machine=${machine:-unknown}" >&2
    exit 2
  }
}
require git
build_yash() {
  require make
  local src="$OUT/src/yash"
  git clone --depth 1 https://github.com/magicant/yash.git "$src"
  (cd "$src" && ./configure --prefix=/usr/local && make -j"${JOBS:-2}" && make install DESTDIR="$OUT/stage")
  install -D -m 0755 "$OUT/stage/usr/local/bin/yash" "$ROOTFS/usr/local/bin/yash"
}
build_nushell() {
  require cargo
  local src="$OUT/src/nushell"
  git clone --depth 1 https://github.com/nushell/nushell.git "$src"
  (cd "$src" && cargo build --release --locked)
  install -D -m 0755 "$src/target/release/nu" "$ROOTFS/usr/local/bin/nu"
}
build_elvish() {
  require go
  local src="$OUT/src/elvish"
  git clone --depth 1 https://github.com/elves/elvish.git "$src"
  (cd "$src" && go build -trimpath -o "$ROOTFS/usr/local/bin/elvish" ./cmd/elvish)
}
build_wezterm() {
  require cargo
  local src="$OUT/src/wezterm"
  git clone --depth 1 https://github.com/wez/wezterm.git "$src"
  (cd "$src" && cargo build --release --locked -p wezterm-gui)
  install -D -m 0755 "$src/target/release/wezterm-gui" "$ROOTFS/usr/local/bin/wezterm"
}
build_ghostty() {
  require python3
  local src="$OUT/src/ghostty" zigver venv
  git clone --depth 1 https://github.com/ghostty-org/ghostty.git "$src"
  zigver="$(tr -d '[:space:]' < "$src/.zig-version")"
  [[ -n "$zigver" ]] || { echo "Ghostty source has no pinned .zig-version" >&2; exit 2; }
  venv="$OUT/zig-venv"
  python3 -m venv "$venv"
  "$venv/bin/pip" install --disable-pip-version-check "ziglang==$zigver"
  (cd "$src" && "$venv/bin/python" -m ziglang build -Doptimize=ReleaseFast)
  install -D -m 0755 "$src/zig-out/bin/ghostty" "$ROOTFS/usr/local/bin/ghostty"
}
build_contour() {
  require cmake; require ninja
  local src="$OUT/src/contour"
  git clone --depth 1 https://github.com/contour-terminal/contour.git "$src"
  cmake -S "$src" -B "$src/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
  cmake --build "$src/build" --parallel "${JOBS:-2}"
  cmake --install "$src/build" --prefix "$OUT/stage/usr/local"
  local binary
  binary="$(find "$OUT/stage/usr/local" "$src/build" -type f -name contour -perm -111 -print -quit)"
  [[ -n "$binary" ]] || { echo "Contour build produced no executable" >&2; exit 2; }
  install -D -m 0755 "$binary" "$ROOTFS/usr/local/bin/contour"
}
tmp="$OUT/providers-built.tsv"
: > "$tmp"
while IFS='|' read -r package binary status; do
  [[ -n "$binary" ]] || continue
  case "$binary" in
    yash) build_yash ;;
    nu) build_nushell ;;
    elvish) build_elvish ;;
    wezterm) build_wezterm ;;
    ghostty) build_ghostty ;;
    contour) build_contour ;;
    *) echo "No genuine source-build recipe for missing provider $package ($binary): $status" >&2; exit 2 ;;
  esac
  test -x "$ROOTFS/usr/local/bin/$binary" || { echo "Source build did not install $binary" >&2; exit 2; }
  verify_target_elf "$ROOTFS/usr/local/bin/$binary"
  case "$binary" in
    yash) commit="$(git -C "$OUT/src/yash" rev-parse HEAD)" ;;
    nu) commit="$(git -C "$OUT/src/nushell" rev-parse HEAD)" ;;
    elvish) commit="$(git -C "$OUT/src/elvish" rev-parse HEAD)" ;;
    wezterm) commit="$(git -C "$OUT/src/wezterm" rev-parse HEAD)" ;;
    ghostty) commit="$(git -C "$OUT/src/ghostty" rev-parse HEAD)" ;;
    contour) commit="$(git -C "$OUT/src/contour" rev-parse HEAD)" ;;
  esac
  case "$binary" in
    yash) srcdir="$OUT/src/yash" ;;
    nu) srcdir="$OUT/src/nushell" ;;
    elvish) srcdir="$OUT/src/elvish" ;;
    wezterm) srcdir="$OUT/src/wezterm" ;;
    ghostty) srcdir="$OUT/src/ghostty" ;;
    contour) srcdir="$OUT/src/contour" ;;
  esac
  install -d "$ROOTFS/usr/share/doc/chimera-terminal-shells/$binary"
  for license in LICENSE COPYING LICENSE.md LICENSE.txt; do
    [[ -s "$srcdir/$license" ]] && install -m 0644 "$srcdir/$license" "$ROOTFS/usr/share/doc/chimera-terminal-shells/$binary/$license"
  done
  digest="$(sha256sum "$ROOTFS/usr/local/bin/$binary" | awk '{print $1}')"
  printf '%s|%s|source-built|%s|%s\n' "$package" "$binary" "$commit" "$digest" >> "$tmp"
done < "$MISSING"
cat "$tmp" >> "$INSTALLED"
: > "$MISSING"
sha256sum "$INSTALLED" "$tmp" > "$ROOTFS/usr/share/chimera/aurora/terminal-shell-build.SHA256SUMS"
while IFS='|' read -r package binary status commit digest; do
  [[ -x "$ROOTFS/usr/local/bin/$binary" ]] && sha256sum "$ROOTFS/usr/local/bin/$binary" >> "$ROOTFS/usr/share/chimera/aurora/terminal-shell-build.SHA256SUMS"
done < "$tmp"
echo "Source-built missing shell and terminal providers; verified executable files and recorded upstream commits."
