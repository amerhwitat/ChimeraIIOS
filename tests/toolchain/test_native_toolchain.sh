#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
required=(gcc g++ as ld ar ranlib nm objcopy objdump readelf strip)
for tool in "${required[@]}"; do command -v "$tool" >/dev/null || { echo "missing: $tool" >&2; exit 1; }; done
CHIMERA_NATIVE_COMPILER=gcc "$ROOT/tools/toolchain/chimera-cc" -std=c11 -Wall -Werror -x c -o "$TMP/c-test" - <<'EOF'
int main(void) { return 0; }
EOF
"$TMP/c-test"
CHIMERA_NATIVE_COMPILER=gcc "$ROOT/tools/toolchain/chimera-cxx" -std=c++20 -Wall -Werror -x c++ -o "$TMP/cxx-test" - <<'EOF'
#include <iostream>
int main() { std::cout << "chimera-native-cxx\n"; return 0; }
EOF
"$TMP/cxx-test"
cat > "$TMP/native.s" <<'EOF'
.text
.globl chimera_native_asm
.type chimera_native_asm,@function
chimera_native_asm:
  mov $7, %eax
  ret
EOF
CHIMERA_ASSEMBLER=gnu "$ROOT/tools/toolchain/chimera-gas" -o "$TMP/native.o" "$TMP/native.s"
test -s "$TMP/native.o"
CHIMERA_NATIVE_LINKER=bfd "$ROOT/tools/toolchain/chimera-ld" --version >/dev/null
echo "native C/C++/ASM/linker toolchain conformance passed"
