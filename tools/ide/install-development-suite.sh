#!/usr/bin/env bash
set -euo pipefail
usage(){ cat <<'EOF'
Usage: install-development-suite.sh [--with-vscodium]
Installs native compilers, assemblers, debuggers, disassemblers and build tools.
VSCodium is installed only when --with-vscodium is explicitly supplied.
EOF
}
WITH_IDE=0
for arg in "$@"; do case "$arg" in --with-vscodium) WITH_IDE=1;; -h|--help) usage; exit 0;; *) echo "Unknown option: $arg" >&2; exit 64;; esac; done
case "$(uname -s)" in
 Linux)
  if command -v apt-get >/dev/null 2>&1; then
   sudo apt-get update
   sudo apt-get install -y build-essential gcc g++ clang llvm lld binutils nasm yasm cmake ninja-build meson pkg-config gdb gdb-multiarch lldb valgrind qemu-user qemu-user-static python3 python3-pip openjdk-21-jdk-headless rustc cargo
  elif command -v dnf >/dev/null 2>&1; then
   sudo dnf install -y gcc gcc-c++ clang llvm lld binutils nasm yasm cmake ninja-build meson pkgconf-pkg-config gdb lldb valgrind qemu-user-static python3 python3-pip java-21-openjdk-devel rust cargo
  elif command -v pacman >/dev/null 2>&1; then
   sudo pacman -Sy --needed --noconfirm base-devel gcc clang llvm lld binutils nasm yasm cmake ninja meson pkgconf gdb lldb valgrind qemu-user-static python python-pip jdk21-openjdk rust
  else echo "Unsupported Linux package manager." >&2; exit 69; fi ;;
 Darwin)
  command -v brew >/dev/null || { echo "Install Homebrew first." >&2; exit 69; }
  brew install llvm lld binutils nasm yasm cmake ninja meson pkg-config gdb rust
  brew install --cask temurin ;;
 MINGW*|MSYS*|CYGWIN*)
  command -v winget >/dev/null || { echo "Install Windows App Installer/winget first." >&2; exit 69; }
  winget install --id Kitware.CMake --exact --accept-package-agreements --accept-source-agreements
  winget install --id Ninja-build.Ninja --exact --accept-package-agreements --accept-source-agreements
  winget install --id NASM.NASM --exact --accept-package-agreements --accept-source-agreements
  winget install --id LLVM.LLVM --exact --accept-package-agreements --accept-source-agreements
  winget install --id MSYS2.MSYS2 --exact --accept-package-agreements --accept-source-agreements ;;
 *) echo "Unsupported host OS: $(uname -s)" >&2; exit 69;;
esac
if [[ "$WITH_IDE" == 1 ]]; then python3 "$(dirname "$0")/install-vscodium.py" --install; fi
echo "Toolchain installation finished. Verify gcc, clang, gdb and cmake versions."
