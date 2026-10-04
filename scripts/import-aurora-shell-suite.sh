#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: scripts/import-aurora-shell-suite.sh

Usage:
  scripts/import-aurora-shell-suite.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${CHIMERA_ROOTFS_DIR:-${ROOT}/build/iso/rootfs}"
PREFIX="${DEST}/usr"
CACHE="${CHIMERA_SHELL_CACHE:-${ROOT}/build/shell-cache}"
MODE="${CHIMERA_SHELL_MODE:-source-first}"
mkdir -p "$PREFIX/bin" "$PREFIX/share/chimera/aurora/shells" "$CACHE"
cp "$ROOT/aurora/shells/registry.json" "$PREFIX/share/chimera/aurora/shells/registry.json"
log(){ printf '[AURORA-SHELL] %s\n' "$*"; }
have(){ command -v "$1" >/dev/null 2>&1; }
copy_if_present(){ local b="$1"; if have "$b"; then cp -L "$(command -v "$b")" "$PREFIX/bin/$b" 2>/dev/null || true; log "Imported existing $b"; return 0; fi; return 1; }
clone(){ local id="$1" url="$2"; local src="$CACHE/src-$id"; if [[ ! -d "$src" ]]; then log "Cloning $id"; git clone --depth 1 "$url" "$src"; fi; printf '%s' "$src"; }
build_source(){
  local id="$1" url="$2" src
  src="$(clone "$id" "$url")"
  case "$id" in
    bash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/bash" "$PREFIX/bin/bash" ;;
    zsh) (cd "$src" && (./Util/preconfig || autoconf) && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/Src/zsh" "$PREFIX/bin/zsh" ;;
    fish) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j"$(nproc)"); cp "$src/build/fish" "$PREFIX/bin/fish" ;;
    dash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/src/dash" "$PREFIX/bin/dash" ;;
    mksh) (cd "$src" && sh Build.sh -r -j"$(nproc)"); find "$src" -type f -name mksh -perm -111 -exec cp {} "$PREFIX/bin/mksh" \; -quit ;;
    elvish) have go || return 1; (cd "$src" && go build -o "$PREFIX/bin/elvish" ./cmd/elvish) ;;
    nushell) have cargo || return 1; (cd "$src" && cargo build --release --bin nu); cp "$src/target/release/nu" "$PREFIX/bin/nu" ;;
    yash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); find "$src" -type f -name yash -perm -111 -exec cp {} "$PREFIX/bin/yash" \; -quit ;;
    *) return 1 ;;
  esac
}
for b in bash zsh fish dash mksh elvish nu yash; do copy_if_present "$b" || true; done
[[ "$MODE" == "binary-only" ]] && { log "Binary-only mode selected; using packages/prebuilt artifacts already present"; exit 0; }
build_source bash https://git.savannah.gnu.org/git/bash.git || log "Bash source build unavailable; keeping system/package Bash"
build_source zsh https://github.com/zsh-users/zsh.git || log "Zsh source build unavailable; keeping system/package Zsh"
build_source fish https://github.com/fish-shell/fish-shell.git || log "fish source build unavailable; keeping system/package fish"
build_source dash https://git.kernel.org/pub/scm/utils/dash/dash.git || log "dash source build unavailable; keeping system/package dash"
build_source mksh https://github.com/MirBSD/mksh.git || log "mksh source build unavailable; keeping system/package mksh"
build_source elvish https://github.com/elves/elvish.git || log "Elvish source build unavailable; keeping system/package Elvish"
build_source nushell https://github.com/nushell/nushell.git || log "Nushell source build unavailable; keeping system/package Nushell"
build_source yash https://github.com/magicant/yash.git || log "Yash source build unavailable; keeping system/package Yash"
log "Shell registry staged at $PREFIX/share/chimera/aurora/shells/registry.json"
