#!/usr/bin/env bash
set -euo pipefail

PREFIX="${CHIMERA_TOOLCHAIN_PREFIX:-/opt/chimera-sdk}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="${PREFIX}/bin"
MANIFEST="${PREFIX}/share/chimera/toolchains/chimera-native-toolchain.json"
mkdir -p "${BIN}" "${PREFIX}/share/chimera/toolchains"

packages=(gcc g++ binutils clang llvm lld nasm make cmake ninja-build pkg-config)
install_apt() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends "${packages[@]}"
}
install_dnf() { dnf install -y "${packages[@]}"; }
install_pacman() { pacman -Sy --noconfirm "${packages[@]}"; }

if [[ "${CHIMERA_SKIP_PACKAGE_INSTALL:-0}" != 1 ]]; then
  if command -v apt-get >/dev/null 2>&1; then install_apt
  elif command -v dnf >/dev/null 2>&1; then install_dnf
  elif command -v pacman >/dev/null 2>&1; then install_pacman
  else echo "No supported package manager; expecting preinstalled native toolchain" >&2
  fi
fi

required=(gcc g++ as ld ar ranlib nm objcopy objdump readelf strip)
for tool in "${required[@]}"; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing required native tool: $tool" >&2; exit 1; }
done
for tool in clang clang++ lld nasm; do
  command -v "$tool" >/dev/null 2>&1 || echo "[WARN] optional tool unavailable: $tool"
done

for wrapper in chimera-cc chimera-cxx chimera-as chimera-ld; do
  install -m 0755 "${ROOT}/tools/toolchain/${wrapper}" "${BIN}/${wrapper}"
done
install -m 0644 "${ROOT}/toolchains/chimera-native-toolchain.json" "${MANIFEST}"

"${BIN}/chimera-cc" --version | head -n 1
"${BIN}/chimera-cxx" --version | head -n 1
"${BIN}/chimera-as" --version | head -n 1
"${BIN}/chimera-ld" --version | head -n 1
echo "Chimera native C/C++/ASM toolchain installed under ${PREFIX}"
