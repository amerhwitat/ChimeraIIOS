#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: scripts/import-aurora-terminal-suite.sh

Usage:
  scripts/import-aurora-terminal-suite.sh [options] [arguments]

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
CACHE="${CHIMERA_TERMINAL_CACHE:-${ROOT}/build/terminal-cache}"
MODE="${CHIMERA_TERMINAL_MODE:-source-first}"
mkdir -p "$PREFIX/bin" "$PREFIX/share/chimera/aurora/terminals" "$PREFIX/share/applications" "$CACHE"
cp "$ROOT/aurora/terminals/registry.json" "$PREFIX/share/chimera/aurora/terminals/registry.json"
log(){ printf '[AURORA-TERMINAL] %s\n' "$*"; }
have(){ command -v "$1" >/dev/null 2>&1; }
install_existing(){ local b="$1"; [[ -x "$PREFIX/bin/$b" ]]; }
source_build(){
  local id="$1" url="$2"; local src="$CACHE/src-$id"
  local binary="$id"
  [[ "$id" == "nushell" ]] && binary=nu
  [[ -x "$PREFIX/bin/$binary" && "${CHIMERA_FORCE_SOURCE_BUILD:-0}" != "1" ]] && { log "$id: verified target package binary already staged"; return 0; }
  if [[ ! -d "$src" ]]; then log "Cloning $id from $url"; git clone --depth 1 "$url" "$src"; fi
  case "$id" in
    xterm) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); install -m 0755 "$src/xterm" "$PREFIX/bin/xterm" ;;
    foot) (cd "$src" && meson setup build --buildtype=release && ninja -C build); install -m 0755 "$src/build/foot" "$PREFIX/bin/foot" ;;
    kitty) (cd "$src" && python3 setup.py linux-package --update-check-interval=0); find "$src" -type f -path '*/bin/kitty' -perm -111 -exec install -m 0755 {} "$PREFIX/bin/kitty" \\; -quit ;;
    gnome-terminal) (cd "$src" && meson setup build --buildtype=release && ninja -C build); find "$src/build" -type f -name gnome-terminal -perm -111 -exec install -m 0755 {} "$PREFIX/bin/gnome-terminal" \\; -quit ;;
    konsole) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j"$(nproc)"); find "$src/build" -type f -name konsole -perm -111 -exec install -m 0755 {} "$PREFIX/bin/konsole" \\; -quit ;;
    xfce4-terminal) (cd "$src" && meson setup build --buildtype=release && ninja -C build); find "$src/build" -type f -name xfce4-terminal -perm -111 -exec install -m 0755 {} "$PREFIX/bin/xfce4-terminal" \\; -quit ;;
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
for b in xterm gnome-terminal konsole xfce4-terminal foot kitty; do install_existing "$b" && log "Target/provider binary available: $b" || log "$b has no staged provider yet"; done
if [[ "$MODE" != "binary-only" ]]; then
  source_build xterm https://github.com/ThomasDickey/xterm-snapshots.git || log "xterm source build unavailable; verified package fallback required"
  source_build gnome-terminal https://gitlab.gnome.org/GNOME/gnome-terminal.git || log "GNOME Terminal source build unavailable; verified package fallback required"
  source_build konsole https://invent.kde.org/utilities/konsole.git || log "Konsole source build unavailable; verified package fallback required"
  source_build xfce4-terminal https://gitlab.xfce.org/apps/xfce4-terminal.git || log "XFCE Terminal source build unavailable; verified package fallback required"
  source_build foot https://codeberg.org/dnkl/foot.git || log "Foot source build unavailable; verified package fallback required"
  source_build kitty https://github.com/kovidgoyal/kitty.git || log "Kitty source build unavailable; verified package fallback required"
  source_build alacritty https://github.com/alacritty/alacritty.git || log "Alacritty source build unavailable; verified package fallback required"
  source_build wezterm https://github.com/wezterm/wezterm.git || log "WezTerm source build unavailable; verified package fallback required"
  source_build contour https://github.com/contour-terminal/contour.git || log "Contour source build unavailable; verified package fallback required"
  source_build ghostty https://github.com/ghostty-org/ghostty.git || log "Ghostty source build unavailable; verified package fallback required"
fi
python3 - "$ROOT" "$PREFIX" "$CACHE" <<'PY'
import hashlib,json,sys
from pathlib import Path
root,prefix,cache=map(Path,sys.argv[1:]); reg=json.loads((root/"aurora/terminals/registry.json").read_text()); rows=[]
for item in reg["entries"]:
 b=prefix/"bin"/item["binary"]; src=cache/("src-"+item["id"]); commit=None
 if (src/".git").exists():
  import subprocess
  try: commit=subprocess.check_output(["git","-C",str(src),"rev-parse","HEAD"],text=True).strip()
  except Exception: pass
 digest=hashlib.sha256(b.read_bytes()).hexdigest() if b.is_file() else None
 rows.append({"id":item["id"],"binary":item["binary"],"status":"built-or-provider-present" if b.is_file() and b.stat().st_mode&0o111 else "provider-missing","source_commit":commit,"sha256":digest})
out=prefix/"share/chimera/aurora/terminals/terminal-build-report.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({"schema":"CHM-TERMINAL-BUILD-REPORT-1","entries":rows},indent=2)+"\n")
print("Terminal source/provider report:",sum(x["status"]=="built-or-provider-present" for x in rows),"/",len(rows))
PY
log "Terminal registry staged at $PREFIX/share/chimera/aurora/terminals/registry.json"
