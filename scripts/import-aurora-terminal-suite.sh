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
CACHE="${CHIMERA_TERMINAL_CACHE:-/var/tmp/chimera-terminal-cache-${UID:-$(id -u)}}"
MODE="${CHIMERA_TERMINAL_MODE:-source-first}"
mkdir -p "$PREFIX/bin" "$PREFIX/share/chimera/aurora/terminals" "$PREFIX/share/applications" "$CACHE"
# Rust/CMake compilation must not put high-churn build artifacts on WSL DrvFs (/mnt/c, /mnt/e).
# Keep an explicit override for CI, but reject known Windows-mounted filesystems.
cache_fstype="$(findmnt -T "$CACHE" -n -o FSTYPE 2>/dev/null || stat -f -c %T "$CACHE" 2>/dev/null || true)"
case "$cache_fstype" in 9p|drvfs|fuseblk|ntfs|ntfs3) log "Terminal cache is on a Windows-mounted filesystem ($cache_fstype): $CACHE"; exit 2;; esac
CARGO_BUILD_JOBS="${CHIMERA_CARGO_BUILD_JOBS:-2}"
[[ "$CARGO_BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || { log "CHIMERA_CARGO_BUILD_JOBS must be a positive integer"; exit 2; }
cp "$ROOT/aurora/terminals/registry.json" "$PREFIX/share/chimera/aurora/terminals/registry.json"
log(){ printf '[AURORA-TERMINAL] %s\n' "$*"; }
have(){ command -v "$1" >/dev/null 2>&1; }
TARGET_ARCH="${CHIMERA_TARGET_ARCH:-$(uname -m)}"
normalize_arch() {
  case "$1" in
    amd64|x86_64) printf x86_64 ;;
    arm64|aarch64) printf aarch64 ;;
    armhf|armv7l|armv7*) printf arm ;;
    i386|i486|i586|i686) printf i386 ;;
    riscv64) printf riscv64 ;;
    ppc64le) printf ppc64le ;;
    s390x) printf s390x ;;
    *) return 1 ;;
  esac
}
verify_target_binary() {
  local binary="$1" arch machine expected
  [[ -x "$binary" ]] || { log "Not executable: $binary"; return 1; }
  command -v readelf >/dev/null 2>&1 || { log "readelf is required to verify $binary"; return 1; }
  arch="$(normalize_arch "$TARGET_ARCH")" || { log "Unsupported target architecture: $TARGET_ARCH"; return 1; }
  machine="$(readelf -h "$binary" 2>/dev/null | sed -n 's/^[[:space:]]*Machine:[[:space:]]*//p')"
  # Some packaged terminal launchers (notably Python entry points) are
  # executable scripts. Verify their shebang interpreter's target ELF rather
  # than incorrectly treating the script text as a native binary.
  if [[ -z "$machine" ]]; then
    local shebang interpreter target_interpreter
    IFS= read -r shebang < "$binary" || shebang=""
    [[ "$shebang" == '#!'* ]] || { log "Not an ELF binary or recognized shebang script: $binary"; return 1; }
    interpreter="${shebang:2}"
    interpreter="${interpreter%% *}"
    if [[ "$interpreter" == "/usr/bin/env" ]]; then
      local env_command
      env_command="$(sed -n '1s/^#![[:space:]]*\/usr\/bin\/env[[:space:]]*//p' "$binary" | awk '{print $1}')"
      [[ -n "$env_command" ]] || { log "Unresolvable env shebang: $binary"; return 1; }
      target_interpreter="$DEST/usr/bin/$env_command"
      [[ -x "$target_interpreter" ]] || target_interpreter="$DEST/bin/$env_command"
    else
      target_interpreter="$DEST$interpreter"
    fi
    [[ -x "$target_interpreter" ]] || { log "Target shebang interpreter missing: $target_interpreter"; return 1; }
    machine="$(readelf -h "$target_interpreter" 2>/dev/null | sed -n 's/^[[:space:]]*Machine:[[:space:]]*//p')"
    [[ -n "$machine" ]] || { log "Target shebang interpreter is not a verified ELF: $target_interpreter"; return 1; }
  fi
  case "$arch" in
    x86_64) expected="Advanced Micro Devices X86-64" ;;
    aarch64) expected="AArch64" ;;
    arm) expected="ARM" ;;
    i386) expected="Intel 80386" ;;
    riscv64) expected="RISC-V" ;;
    ppc64le) expected="PowerPC64" ;;
    s390x) expected="IBM S/390" ;;
  esac
  [[ "$machine" == "$expected" ]] || { log "Architecture mismatch for $binary: target=$TARGET_ARCH ELF=$machine"; return 1; }
}
require_native_build_arch() {
  local host target
  host="$(normalize_arch "$(uname -m)")" || return 1
  target="$(normalize_arch "$TARGET_ARCH")" || return 1
  [[ "$host" == "$target" ]] || { log "Refusing host-native source build for target $TARGET_ARCH (build host $(uname -m)); use a real cross toolchain or target provider package"; return 1; }
}
install_existing(){ local b="$1"; local p; for p in "$PREFIX/bin/$b" "$DEST/bin/$b" "$DEST/usr/local/bin/$b"; do if [[ -x "$p" ]] && verify_target_binary "$p"; then log "Verified target-rootfs provider: $p"; return 0; fi; done; log "$b has no verified target-rootfs provider"; return 1; }
source_build(){
  require_native_build_arch || return 1;
<<<<<<< HEAD
  local id="$1" url="$2"; local src="$CACHE/src-$id"
  if [[ ! -d "$src" ]]; then log "Cloning $id from $url"; git clone --depth 1 "$url" "$src"; fi
  case "$id" in
    alacritty) (cd "$src" && cargo build --release); cp "$src/target/release/alacritty" "$PREFIX/bin/" ;;
    wezterm) (cd "$src" && cargo build --release --bin wezterm-gui); install -m 0755 "$src/target/release/wezterm-gui" "$PREFIX/bin/wezterm" ;;
    contour) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && cmake --build build -j"$(nproc)"); find "$src/build" -type f -name contour -perm -111 -exec cp {} "$PREFIX/bin/contour" \; -quit ;;
=======
  local id="$1" url="$2"; local src="$CACHE/src-$id"; local cargo_target="$CACHE/cargo-target-$id"
  if [[ ! -d "$src/.git" ]]; then
    rm -rf "$src"
    if [[ "$id" == "alacritty" ]]; then
      # Pin a release whose Rust and system-library requirements are known for
      # Ubuntu 24.04; do not build an unbounded upstream default branch.
      log "Cloning Alacritty v0.13.2 from $url"
      git clone --depth 1 --branch v0.13.2 "$url" "$src"
    else
      log "Cloning $id from $url"
      git clone --depth 1 "$url" "$src"
    fi
  fi
  case "$id" in
    alacritty)
      have cargo || { log "Cargo is required for the pinned Alacritty source build"; return 1; }
      (cd "$src" && CARGO_TARGET_DIR="$cargo_target" CARGO_BUILD_JOBS="$CARGO_BUILD_JOBS" cargo build --release --locked)
      install -m 0755 "$cargo_target/release/alacritty" "$PREFIX/bin/alacritty"
      ;;
    wezterm) (cd "$src" && CARGO_TARGET_DIR="$cargo_target" CARGO_BUILD_JOBS="$CARGO_BUILD_JOBS" cargo build --release --bin wezterm-gui); install -m 0755 "$cargo_target/release/wezterm-gui" "$PREFIX/bin/wezterm" ;;
    contour) rm -rf "$src/build"; (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && cmake --build build --parallel "$CARGO_BUILD_JOBS"); find "$src/build" -type f -name contour -perm -111 -exec cp {} "$PREFIX/bin/contour" \; -quit ;;
>>>>>>> ed33d19e9 (fix(aurora): move terminal build cache off WSL DrvFs)
    ghostty)
      have python3 || return 1
      local zigver venv
      [[ -f "$src/.zig-version" ]] || { log "Ghostty source has no pinned .zig-version"; return 1; }
      zigver="$(tr -d '[:space:]' < "$src/.zig-version")"
      [[ -n "$zigver" ]] || { log "Ghostty source has an empty .zig-version"; return 1; }
      venv="$CACHE/zig-venv"
      python3 -m venv "$venv"
      "$venv/bin/pip" install --disable-pip-version-check "ziglang==$zigver"
      (cd "$src" && "$venv/bin/python" -m ziglang build -Doptimize=ReleaseFast)
      cp "$src/zig-out/bin/ghostty" "$PREFIX/bin/" ;;

    fish) (cd "$src" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j"$(nproc)"); cp "$src/build/fish" "$PREFIX/bin/" ;;
    zsh) (cd "$src" && ./Util/preconfig || autoconf && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/Src/zsh" "$PREFIX/bin/" ;;
    bash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/bash" "$PREFIX/bin/" ;;
    dash) (cd "$src" && ./configure --prefix=/usr && make -j"$(nproc)"); cp "$src/src/dash" "$PREFIX/bin/" ;;
    mksh) (cd "$src" && sh Build.sh -r -j"$(nproc)"); find "$src" -type f -name mksh -perm -111 -exec cp {} "$PREFIX/bin/mksh" \; -quit ;;
    elvish) (cd "$src" && go build -o "$PREFIX/bin/elvish" ./cmd/elvish);;
    nushell) (cd "$src" && CARGO_TARGET_DIR="$cargo_target" CARGO_BUILD_JOBS="$CARGO_BUILD_JOBS" cargo build --release --bin nu); cp "$cargo_target/release/nu" "$PREFIX/bin/" ;;
    *) return 1;;
  esac
  local built
  case "$id" in kitty) built="$PREFIX/bin/kitty";; *) built="$PREFIX/bin/$id";; esac
  verify_target_binary "$built" || { rm -f "$built"; return 1; }
}
# Prefer distro-provided binaries for desktop terminals; source builds are enabled for projects with reliable recipes.
for b in xterm gnome-terminal konsole xfce4-terminal foot kitty; do install_existing "$b" || log "$b remains unavailable until a matching target package is staged"; done
if [[ "$MODE" != "binary-only" ]]; then
  source_build alacritty https://github.com/alacritty/alacritty.git || log "Alacritty source build unavailable; package/binary fallback required"
  source_build wezterm https://github.com/wezterm/wezterm.git || log "WezTerm source build unavailable; package/binary fallback required"
  source_build contour https://github.com/contour-terminal/contour.git || log "Contour source build unavailable; package/binary fallback required"
  source_build ghostty https://github.com/ghostty-org/ghostty.git || log "Ghostty source build unavailable; package/binary fallback required"
fi
# The desktop registry is only complete when every entry resolves to a real
# executable for this target architecture. Missing providers stop ISO staging.
for binary in xterm gnome-terminal konsole xfce4-terminal foot kitty \
              alacritty wezterm ghostty contour ptyxis terminator kgx tilix \
              mate-terminal qterminal sakura terminology lxterminal blackbox; do
  install_existing "$binary" || { log "REQUIRED TERMINAL PROVIDER MISSING: $binary"; exit 2; }
done
log "All 20 Aurora terminal binaries are present and target-architecture verified."
log "Terminal registry staged at $PREFIX/share/chimera/aurora/terminals/registry.json"
