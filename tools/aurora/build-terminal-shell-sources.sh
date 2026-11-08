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
TARGET_ARCH="${CHIMERA_TARGET_ARCH:-}"
if [[ -z "$TARGET_ARCH" ]]; then
  target_dpkg="$(chroot "$ROOTFS" dpkg --print-architecture 2>/dev/null || true)"
  case "$target_dpkg" in
    amd64) TARGET_ARCH=x86_64 ;; i386) TARGET_ARCH=i686 ;; armel) TARGET_ARCH=armel ;;
    armhf) TARGET_ARCH=armv7 ;; arm64) TARGET_ARCH=aarch64 ;; riscv64) TARGET_ARCH=riscv64 ;;
    ppc64el) TARGET_ARCH=ppc64le ;; s390x) TARGET_ARCH=s390x ;; *) TARGET_ARCH="$(uname -m)" ;;
  esac
fi
host_arch="$(uname -m)"
if [[ "$TARGET_ARCH" != "$host_arch" ]]; then
  echo "Source terminal builds are native-host only (host=$host_arch target=$TARGET_ARCH); install target-architecture packages or provide an explicit cross-build recipe." >&2
  exit 2
fi
verify_target_elf() {
  local binary="$1" machine expected
  require readelf
  case "$TARGET_ARCH" in
    x86_64|amd64) expected="Advanced Micro Devices X86-64" ;;
    aarch64|arm64) expected="AArch64" ;;
    armel|armv7|armv7l|armhf) expected="ARM" ;;
    riscv64) expected="RISC-V" ;;
    i686|i386) expected="Intel 80386" ;; ppc64le) expected="PowerPC64" ;; s390x) expected="IBM S/390" ;;
    *) echo "Unsupported CHIMERA_TARGET_ARCH=$TARGET_ARCH; refusing unverified provider" >&2; exit 2 ;;
  esac
  machine="$(readelf -h "$binary" | awk -F: '/^[[:space:]]*Machine:/ {sub(/^[[:space:]]+/, "", $2); print $2}')"
  [[ -n "$machine" && "$machine" == *"$expected"* ]] || {
    echo "Provider architecture mismatch: $binary target=$TARGET_ARCH ELF machine=${machine:-unknown}" >&2
    exit 2
  }
}
require git
build_bash() {
  require make; require gcc
  local src="$OUT/src/bash"
  git clone --depth 1 https://git.savannah.gnu.org/git/bash.git "$src"
  (cd "$src" && ./configure --prefix=/usr/local --without-bash-malloc && make -j"${JOBS:-2}" && make install DESTDIR="$OUT/stage")
  install -D -m 0755 "$OUT/stage/usr/local/bin/bash" "$ROOTFS/usr/local/bin/bash"
}
build_zsh() {
  require make; require gcc; require autoconf
  local src="$OUT/src/zsh"
  git clone --depth 1 https://github.com/zsh-users/zsh.git "$src"
  (cd "$src" && ./Util/preconfig && ./configure --prefix=/usr/local && make -j"${JOBS:-2}" && make install DESTDIR="$OUT/stage")
  install -D -m 0755 "$OUT/stage/usr/local/bin/zsh" "$ROOTFS/usr/local/bin/zsh"
}
build_fish() {
  require cmake; require ninja; require c++
  local src="$OUT/src/fish"
  git clone --depth 1 https://github.com/fish-shell/fish-shell.git "$src"
  cmake -S "$src" -B "$src/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_DOCS=OFF
  cmake --build "$src/build" --parallel "${JOBS:-2}"
  DESTDIR="$OUT/stage" cmake --install "$src/build"
  install -D -m 0755 "$OUT/stage/usr/local/bin/fish" "$ROOTFS/usr/local/bin/fish"
}
build_dash() {
  require make; require gcc; require autoreconf
  local src="$OUT/src/dash"
  git clone --depth 1 https://git.kernel.org/pub/scm/utils/dash/dash.git "$src"
  (cd "$src" && if [[ -x ./autogen.sh ]]; then ./autogen.sh; else autoreconf -fi; fi && ./configure --prefix=/usr/local && make -j"${JOBS:-2}" && make install DESTDIR="$OUT/stage")
  install -D -m 0755 "$OUT/stage/usr/local/bin/dash" "$ROOTFS/usr/local/bin/dash"
}
build_mksh() {
  require make; require gcc
  local src="$OUT/src/mksh"
  git clone --depth 1 https://github.com/MirBSD/mksh.git "$src"
  (cd "$src" && sh Build.sh -r)
  local binary
  binary="$(find "$src" -maxdepth 2 -type f -name mksh -perm -111 -print -quit)"
  [[ -n "$binary" ]] || { echo "mksh source build produced no executable" >&2; exit 2; }
  install -D -m 0755 "$binary" "$ROOTFS/usr/local/bin/mksh"
}
build_alacritty() {
  require cargo
  local src="$OUT/src/alacritty"
  git clone --depth 1 https://github.com/alacritty/alacritty.git "$src"
  (cd "$src" && cargo build --release --locked)
  install -D -m 0755 "$src/target/release/alacritty" "$ROOTFS/usr/local/bin/alacritty"
}
build_foot() {
  require meson; require ninja
  local src="$OUT/src/foot"
  git clone --depth 1 https://codeberg.org/dnkl/foot.git "$src"
  meson setup "$src/build" "$src" --buildtype=release --prefix=/usr/local
  ninja -C "$src/build" -j"${JOBS:-2}"
  DESTDIR="$OUT/stage" ninja -C "$src/build" install
  install -D -m 0755 "$OUT/stage/usr/local/bin/foot" "$ROOTFS/usr/local/bin/foot"
}
build_blackbox() {
  require meson; require ninja; require curl; require tar; require patch
  local src="$OUT/src/blackbox" archive
  # Use the upstream Flathub-pinned release archive; GitLab clone URLs may
  # request credentials in non-interactive CI. Verify the archive before use.
  archive="$OUT/blackbox-v0.14.0.tar.gz"
  curl --fail --location --retry 3 --retry-delay 2 \
    "https://gitlab.gnome.org/raggesilver/blackbox/-/archive/v0.14.0/blackbox-v0.14.0.tar.gz" \
    --output "$archive"
  echo "0a8b76666ac71a6dc9e05b8084e1c6c53cda880ad1f8f778d9d5de9a6644ad0d  $archive" | sha256sum --check -
  mkdir -p "$src"
  tar -xzf "$archive" -C "$src" --strip-components=1
  patch -d "$src" -p1 < "$REPO_DIR/live-image/patches/blackbox-gcc14.patch"
  patch -d "$src" -p1 < "$REPO_DIR/live-image/patches/blackbox-appdata.patch"
  meson setup "$src/build" "$src" --buildtype=release --prefix=/usr/local
  ninja -C "$src/build" -j"${JOBS:-2}"
  DESTDIR="$OUT/stage" ninja -C "$src/build" install
  local binary
  binary="$(find "$OUT/stage/usr/local" "$src/build" -type f -name blackbox -perm -111 -print -quit)"
  [[ -n "$binary" ]] || { echo "Black Box source build produced no executable" >&2; exit 2; }
  install -D -m 0755 "$binary" "$ROOTFS/usr/local/bin/blackbox"
}
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
  # WezTerm's workspace includes git submodules. A shallow non-recursive
  # clone leaves Cargo members missing and fails before compilation.
  git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/wez/wezterm.git "$src"
  git -C "$src" submodule update --init --recursive
  local cargo_cmd=(cargo)
  if command -v rustup >/dev/null 2>&1; then
    # WezTerm's current Cargo workspace uses edition 2024, requiring Cargo 1.85+.
    rustup toolchain install stable --profile minimal
    cargo_cmd=(rustup run stable cargo)
  else
    local cargo_version
    cargo_version="$(cargo --version | awk '{print $2}')"
    python3 - "$cargo_version" <<'PY_CARGO_VERSION'
import sys
parts=tuple(int(x) for x in sys.argv[1].split(".")[:3])
if parts < (1,85,0):
    raise SystemExit(f"WezTerm requires Cargo 1.85+ (edition 2024); found {sys.argv[1]}. Install rustup stable.")
PY_CARGO_VERSION
  fi
  "${cargo_cmd[@]}" --version
  (cd "$src" && "${cargo_cmd[@]}" build --release --locked --bin wezterm)
  install -D -m 0755 "$src/target/release/wezterm" "$ROOTFS/usr/local/bin/wezterm"
}
build_ghostty() {
  require python3; require curl; require minisign; require tar
  local src="$OUT/src/ghostty" zigver venv version archive pubkey
  # Use the official release source archive, not a Git checkout: release
  # archives contain preprocessed Blueprint outputs and avoid a host-only
  # development dependency on blueprint-compiler >= 0.16.
  version="${CHIMERA_GHOSTTY_VERSION:-1.3.0}"
  archive="$OUT/ghostty-$version.tar.gz"
  pubkey="RWQlAjJC23149WL2sEpT/l0QKy7hMIFhYdQOFy0Z7z7PbneUgvlsnYcV"
  curl --fail --location --retry 3 --retry-delay 2 \
    "https://release.files.ghostty.org/$version/ghostty-$version.tar.gz" \
    --output "$archive"
  curl --fail --location --retry 3 --retry-delay 2 \
    "https://release.files.ghostty.org/$version/ghostty-$version.tar.gz.minisig" \
    --output "$archive.minisig"
  minisign -Vm "$archive" -P "$pubkey"
  mkdir -p "$src"
  tar -xzf "$archive" -C "$src" --strip-components=1
  # Derive Zig from the authenticated release source metadata.
  if [[ -s "$src/.zig-version" ]]; then
    zigver="$(tr -d '[:space:]' < "$src/.zig-version")"
  elif [[ -s "$src/build.zig.zon" ]]; then
    zigver="$(grep -E 'minimum_zig_version' "$src/build.zig.zon" | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/' | head -n 1)"
  elif [[ -s "$src/build.zig" ]]; then
    zigver="$(grep -E 'required_zig' "$src/build.zig" | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/' | head -n 1)"
  else
    zigver=""
  fi
  [[ -n "$zigver" ]] || { echo "Authenticated Ghostty release has no parseable Zig version contract" >&2; exit 2; }
  venv="$OUT/zig-venv"
  python3 -m venv "$venv"
  "$venv/bin/pip" install --disable-pip-version-check "ziglang==$zigver"
  (cd "$src" && "$venv/bin/python" -m ziglang build -Doptimize=ReleaseFast -fno-sys=gtk4-layer-shell)
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
    bash) build_bash ;;
    zsh) build_zsh ;;
    fish) build_fish ;;
    dash) build_dash ;;
    mksh) build_mksh ;;
    yash) build_yash ;;
    nu) build_nushell ;;
    elvish) build_elvish ;;
    alacritty) build_alacritty ;;
    foot) build_foot ;;
    blackbox) build_blackbox ;;
    wezterm) build_wezterm ;;
    ghostty) build_ghostty ;;
    contour) build_contour ;;
    *) echo "No genuine source-build recipe for missing provider $package ($binary): $status" >&2; exit 2 ;;
  esac
  test -x "$ROOTFS/usr/local/bin/$binary" || { echo "Source build did not install $binary" >&2; exit 2; }
  # The terminal service adapters use stable /usr/bin paths even when the
  # upstream source build installs under /usr/local/bin.
  if [[ ! -e "$ROOTFS/usr/bin/$binary" ]]; then
    install -d "$ROOTFS/usr/bin"
    ln -s "/usr/local/bin/$binary" "$ROOTFS/usr/bin/$binary"
  fi
  verify_target_elf "$ROOTFS/usr/local/bin/$binary"
  case "$binary" in
    bash) commit="$(git -C "$OUT/src/bash" rev-parse HEAD)" ;;
    zsh) commit="$(git -C "$OUT/src/zsh" rev-parse HEAD)" ;;
    fish) commit="$(git -C "$OUT/src/fish" rev-parse HEAD)" ;;
    dash) commit="$(git -C "$OUT/src/dash" rev-parse HEAD)" ;;
    mksh) commit="$(git -C "$OUT/src/mksh" rev-parse HEAD)" ;;
    alacritty) commit="$(git -C "$OUT/src/alacritty" rev-parse HEAD)" ;;
    foot) commit="$(git -C "$OUT/src/foot" rev-parse HEAD)" ;;
    blackbox) commit="$(git -C "$OUT/src/blackbox" rev-parse HEAD)" ;;
    yash) commit="$(git -C "$OUT/src/yash" rev-parse HEAD)" ;;
    nu) commit="$(git -C "$OUT/src/nushell" rev-parse HEAD)" ;;
    elvish) commit="$(git -C "$OUT/src/elvish" rev-parse HEAD)" ;;
    wezterm) commit="$(git -C "$OUT/src/wezterm" rev-parse HEAD)" ;;
    ghostty) commit="release-v1.3.0+sha256:$(sha256sum "$OUT/ghostty-1.3.0.tar.gz" | awk '{print $1}')" ;;
    contour) commit="$(git -C "$OUT/src/contour" rev-parse HEAD)" ;;
  esac
  case "$binary" in
    bash) srcdir="$OUT/src/bash" ;;
    zsh) srcdir="$OUT/src/zsh" ;;
    fish) srcdir="$OUT/src/fish" ;;
    dash) srcdir="$OUT/src/dash" ;;
    mksh) srcdir="$OUT/src/mksh" ;;
    alacritty) srcdir="$OUT/src/alacritty" ;;
    foot) srcdir="$OUT/src/foot" ;;
    blackbox) srcdir="$OUT/src/blackbox" ;;
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
