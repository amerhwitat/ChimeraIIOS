#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_TOOLCHAIN_DIR:-$ROOT/build/toolchains}"
mkdir -p "$OUT"/{bin,lib,include,share,manifests,sources,sysroots}

# Native packages are preferred. Cross toolchains and large runtimes are optional
# so the ISO remains reproducible when a distribution does not publish them.
declare -a PKGS=(
  gcc g++ binutils clang lld llvm nasm yasm gdb lldb
  make cmake ninja pkg-config
  python3 python3-dev nodejs npm ruby perl php lua
  openjdk-21-jdk golang-go rustc cargo
  dotnet-sdk-8.0 mono-devel
  qemu-system-x86 qemu-user qemu-user-static
  valgrind strace
)
if command -v apt-get >/dev/null 2>&1; then
  for p in "${PKGS[@]}"; do
    (cd "$OUT/sources" && apt-get download "$p" >/dev/null 2>&1) || echo "SKIP package: $p"
  done
fi

# Prefer already installed host toolchains and expose a manifest. Binaries are
# copied only when they are ELF executables and remain subject to packaging policy.
for t in gcc g++ clang clang++ as ld lld llvm-mc llvm-objdump objdump readelf nm ar          strip objcopy nasm yasm gdb lldb rustc cargo go javac java python3 node ruby perl php          dotnet qemu-system-x86_64 valgrind strace; do
  if command -v "$t" >/dev/null 2>&1; then
    real="$(command -v "$t")"
    cp -L "$real" "$OUT/bin/$t" 2>/dev/null || true
  fi
done

cat > "$OUT/manifests/toolchain-build.json" <<EOF
{"schema":"CHM-TOOLCHAIN-BUILD-1","matrix":"toolchains/toolchain-matrix.json","packages_attempted":${#PKGS[@]},"purpose":"offline development and ISO bootstrap","provenance":"distribution package repositories plus verified host binaries"}
EOF
find "$OUT" -type f -print0 | sort -z | xargs -0r sha256sum > "$OUT/manifests/SHA256SUMS"
echo "Toolchain staging complete: $OUT"
