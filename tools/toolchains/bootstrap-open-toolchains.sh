#!/usr/bin/env bash
set -euo pipefail
usage() {
  echo "Usage: bash tools/toolchains/bootstrap-open-toolchains.sh list|install|verify"
  echo "Installs reviewed compiler, assembler, disassembler, linker, debugger and QEMU packages."
}
if [ "$#" -eq 0 ]; then usage; exit 0; fi
action="$1"
apt_packages="build-essential gcc-multilib clang llvm lld lldb gdb gdb-multiarch binutils binutils-multiarch nasm yasm cmake ninja-build pkg-config qemu-user qemu-user-static valgrind gcc-aarch64-linux-gnu g++-aarch64-linux-gnu gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf gcc-riscv64-linux-gnu g++-riscv64-linux-gnu gcc-powerpc64le-linux-gnu g++-powerpc64le-linux-gnu gcc-s390x-linux-gnu g++-s390x-linux-gnu gcc-mipsel-linux-gnu g++-mipsel-linux-gnu"
case "$action" in
  list) printf '%s\n' "$apt_packages" | tr ' ' '\n' ;;
  install)
    if command -v apt-get >/dev/null 2>&1; then
      if [ "$(id -u)" -eq 0 ]; then SUDO=; elif command -v sudo >/dev/null 2>&1; then SUDO=sudo; else echo "Run as root or install sudo." >&2; exit 77; fi
      $SUDO apt-get update
      available=""
      for package in $apt_packages; do
        if apt-cache show "$package" >/dev/null 2>&1; then available="$available $package"; else printf 'not available: %s\n' "$package"; fi
      done
      if [ -z "$available" ]; then echo "No reviewed packages available." >&2; exit 69; fi
      $SUDO apt-get install -y $available
    elif command -v brew >/dev/null 2>&1; then
      brew install llvm nasm yasm cmake ninja qemu
    elif command -v winget >/dev/null 2>&1; then
      winget install --id LLVM.LLVM --exact --accept-package-agreements --accept-source-agreements
      winget install --id NASM.NASM --exact --accept-package-agreements --accept-source-agreements
      winget install --id Kitware.CMake --exact --accept-package-agreements --accept-source-agreements
      winget install --id Ninja-build.Ninja --exact --accept-package-agreements --accept-source-agreements
    else echo "No supported package manager found." >&2; exit 69; fi
    ;;
  verify)
    for tool in gcc g++ clang llvm-objdump llvm-readobj llvm-mc as ld objdump readelf nm ar nasm yasm gdb gdb-multiarch lldb qemu-aarch64 qemu-riscv64; do
      if command -v "$tool" >/dev/null 2>&1; then printf 'available: %s\n' "$tool"; else printf 'missing: %s\n' "$tool"; fi
    done
    ;;
  *) usage >&2; exit 64 ;;
esac
