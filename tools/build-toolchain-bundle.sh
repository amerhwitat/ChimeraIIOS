#!/usr/bin/env bash
set -euo pipefail

ROOT="\$(cd -- "\$(dirname -- "\${BASH_SOURCE[0]}")/.." && pwd)"
OUT="\${CHIMERA_TOOLCHAIN_DIR:-\$ROOT/build/toolchains}"
mkdir -p "\$OUT"/{bin,lib,include,share,manifests,sources,sysroots}

declare -a PKGS=(
  gcc g++ binutils clang lld llvm nasm yasm gdb lldb make cmake ninja-build pkg-config
  python3 python3-dev nodejs npm ruby perl php lua5.4
  openjdk-21-jdk golang-go rustc cargo mono-devel
  dotnet-sdk-8.0 qemu-system-x86 qemu-user qemu-user-static valgrind strace
  gcc-aarch64-linux-gnu g++-aarch64-linux-gnu gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
)

# Package staging never installs or updates the developer's WSL host.
# apt-get update/install would modify /var/lib/apt and /var/cache/apt and require root.
APT_ROOT="\$OUT/.apt"
APT_STATE="\$APT_ROOT/state"
APT_LISTS="\$APT_STATE/lists"
APT_CACHE="\$APT_ROOT/cache"
mkdir -p "\$APT_LISTS/partial" "\$APT_CACHE/archives/partial"

prepare_apt_sandbox() {
  if [[ -d /var/lib/apt/lists ]]; then
    find /var/lib/apt/lists -maxdepth 1 -type f -readable -exec cp -f -- {} "\$APT_LISTS/" \; 2>/dev/null || true
  fi
  if [[ -r /var/lib/dpkg/status ]]; then
    cp -f /var/lib/dpkg/status "\$APT_STATE/status"
  fi
}

apt_has() {
  local package="\$1"
  command -v apt-cache >/dev/null 2>&1 || return 1
  apt-cache show "\$package" >/dev/null 2>&1
}

apt_download() {
  local package="\$1"
  apt_has "\$package" || return 1
  local apt_opts=(
    "-o" "Debug::NoLocking=true"
    "-o" "Dir::State=\$APT_STATE"
    "-o" "Dir::State::lists=\$APT_LISTS"
    "-o" "Dir::State::status=\$APT_STATE/status"
    "-o" "Dir::Cache=\$APT_CACHE"
    "-o" "Dir::Cache::archives=\$OUT/sources"
    "-o" "Dir::Cache::pkgcache=\$APT_CACHE/pkgcache.bin"
    "-o" "Dir::Cache::srcpkgcache=\$APT_CACHE/srcpkgcache.bin"
    "-o" "Dir::Etc::sourcelist=/etc/apt/sources.list"
    "-o" "Dir::Etc::sourceparts=/etc/apt/sources.list.d"
    "-o" "Acquire::Languages=none"
  )
  (
    cd "\$OUT/sources"
    apt-get "\${apt_opts[@]}" download "\$package" >/dev/null 2>&1
  )
}

if command -v apt-get >/dev/null 2>&1; then
  prepare_apt_sandbox

  # Existing package indexes are used read-only. Never run apt-get update/install.
  for p in gcc g++ binutils clang lld llvm nasm make cmake pkg-config \
           python3 gcc-aarch64-linux-gnu g++-aarch64-linux-gnu \
           gcc-riscv64-linux-gnu g++-riscv64-linux-gnu; do
    apt_download "\$p" || true
  done

  apt_download ninja-build || echo "WARN package: ninja-build unavailable"
  apt_download lua5.4 || echo "WARN package: lua5.4 unavailable"
  if ! apt_download qemu-user-static; then
    apt_download qemu-user || echo "WARN package: qemu-user-static/qemu-user unavailable"
  fi

  if ! apt_download dotnet-sdk-8.0; then
    echo "INFO package: dotnet-sdk-8.0 unavailable from configured apt sources; using official .NET 8 bootstrap"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL --retry 3 https://dot.net/v1/dotnet-install.sh \
        -o "\$OUT/sources/dotnet-install.sh" || true
      if [[ -s "\$OUT/sources/dotnet-install.sh" ]]; then
        chmod +x "\$OUT/sources/dotnet-install.sh"
        "\$OUT/sources/dotnet-install.sh" --channel 8.0 --install-dir "\$OUT/dotnet" --no-path || true
      fi
    fi
  fi

  for p in "\${PKGS[@]}"; do
    apt_download "\$p" || true
  done
fi

for t in gcc g++ clang clang++ as ld ld.lld lld llvm-mc llvm-objdump objdump readelf nm ar strip objcopy \
         nasm yasm gdb lldb rustc cargo go javac java python3 node ruby perl php dotnet \
         qemu-system-x86_64 qemu-x86_64 valgrind strace aarch64-linux-gnu-g++ riscv64-linux-gnu-g++; do
  command -v "\$t" >/dev/null 2>&1 && cp -L "\$(command -v "\$t")" "\$OUT/bin/\$t" 2>/dev/null || true
done

cat > "\$OUT/manifests/toolchain-build.json" <<EOF
{"schema":"CHM-TOOLCHAIN-BUILD-3","matrix":"toolchains/toolchain-matrix.json","packages_attempted":\${#PKGS[@]},"aliases":{"ninja":"ninja-build","lua":"lua5.4","qemu-user-static":"qemu-user-static|qemu-user"},"cross":{"aarch64":["gcc-aarch64-linux-gnu","g++-aarch64-linux-gnu"],"riscv64":["gcc-riscv64-linux-gnu","g++-riscv64-linux-gnu"]},"dotnet":"dotnet-sdk-8.0","purpose":"offline development, cross compilation and ISO bootstrap","provenance":"distribution package repositories plus verified host binaries","host_apt_mutation":false}
EOF

for wrapper in chimera-cc chimera-cxx chimera-gas chimera-ld; do
  install -m 0755 "\$ROOT/tools/toolchain/\$wrapper" "\$OUT/bin/\$wrapper"
done
install -m 0644 "\$ROOT/toolchains/chimera-native-toolchain.json" "\$OUT/manifests/chimera-native-toolchain.json"
find "\$OUT" -type f ! -path "\$OUT/manifests/SHA256SUMS" -print0 | sort -z | xargs -0r sha256sum > "\$OUT/manifests/SHA256SUMS"
echo "Toolchain staging complete: \$OUT"
