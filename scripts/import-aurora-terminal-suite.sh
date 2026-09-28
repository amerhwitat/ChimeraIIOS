#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${CHIMERA_ROOTFS_DIR:-${ROOT}/build/iso/rootfs}"
PREFIX="${DEST}/usr"
CACHE="${CHIMERA_TERMINAL_CACHE:-${ROOT}/build/terminal-cache}"
MODE="${CHIMERA_TERMINAL_MODE:-source-first}"
mkdir -p "$PREFIX/bin" "$PREFIX/share/chimera/aurora/terminals" "$PREFIX/share/applications" "$CACHE"
cp "$ROOT/aurora/terminals/registry.json" "$PREFIX/share/chimera/aurora/terminals/registry.json"
log(){ printf '[AURORA-TERMINAL] %s\n' "$*"; }
have(){ command -v "$1" >/dev/null 2>&1; }
install_existing(){ local b="$1"; if have "$b"; then cp -L "$(command -v "$b")" "$PREFIX/bin/$b" 2>/dev/null || true; return 0; fi; return 1; }
source_build(){
  local id="$1" url="$2"; local src="$CACHE/src-$id"
  if [[ ! -d "$src" ]]; then log "Cloning $id from $url"; git clone --depth 1 "$url" "$src"; fi
  case "$id" in
    alacritty) (cd "$src" && cargo build --release); cp "$src/target/release/alacritty" "$PREFIX/bin/" ;;
    wezterm) (cd "$src" && cargo build --release --bin wezterm); cp "$src/target/release/wezterm" "$PREFIX/bin/" ;;
    contour) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j"$(nproc)"); find "$src/build" -type f -name contour -perm -111 -exec cp {} "$PREFIX/bin/contour" \; -quit ;;
    ghostty) have zig || return 1; (cd "$src" && zig build -Doptimize=ReleaseFast); cp "$src/zig-out/bin/ghostty" "$PREFIX/bin/" ;;
    fish) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j"$(nproc)"); cp "$src/build/fish" "$PREFIX/bin/" ;;
    zsh) (cd "$src" && ./Util/preconfig || autoconf && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/Src/zsh" "$PREFIX/bin/" ;;
    bash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/bash" "$PREFIX/bin/" ;;
    dash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/src/dash" "$PREFIX/bin/" ;;
    mksh) (cd "$src" && sh Build.sh -r -j"$(nproc)"); find "$src" -type f -name mksh -perm -111 -exec cp {} "$PREFIX/bin/mksh" \; -quit ;;
    elvish) (cd "$src" && go build -o "$PREFIX/bin/elvish" ./cmd/elvish);;
    nushell) (cd "$src" && cargo build --release --bin nu); cp "$src/target/release/nu" "$PREFIX/bin/" ;;
    *) return 1;;
  esac
}
# Prefer distro-provided binaries for desktop terminals; source builds are enabled for projects with reliable recipes.
for b in xterm gnome-terminal konsole xfce4-terminal foot kitty; do install_existing "$b" && log "Imported existing $b" || log "$b will be provided by the target package/build environment"; done
if [[ "$MODE" != "binary-only" ]]; then
  source_build alacritty https://github.com/alacritty/alacritty.git || log "Alacritty source build unavailable; package/binary fallback required"
  source_build wezterm https://github.com/wezterm/wezterm.git || log "WezTerm source build unavailable; package/binary fallback required"
  source_build contour https://github.com/contour-terminal/contour.git || log "Contour source build unavailable; package/binary fallback required"
  source_build ghostty https://github.com/ghostty-org/ghostty.git || log "Ghostty source build unavailable; package/binary fallback required"
fi
log "Terminal registry staged at $PREFIX/share/chimera/aurora/terminals/registry.json"
