#!/usr/bin/env bash
# Rebuild (or verify) the derived Chimera-native ISA catalogue, format
# descriptors and engineering conformance evidence. This script never modifies
# the official isa/generated/universal-instruction-catalog.json baseline.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:---write}"

case "$MODE" in
  --write|--check) ;;
  *) echo "usage: $0 [--write|--check]" >&2; exit 2 ;;
esac

echo "Chimera native ISA self-test (${MODE})"
python3 "$ROOT/tools/isa/chimera_native_isa.py" assemble --arch x86-64 'ADD [RAX],RAX' >/dev/null
python3 "$ROOT/tools/isa/chimera_native_isa.py" assemble --arch aarch64 'ADD X0,X1,X2' >/dev/null
python3 "$ROOT/tools/isa/chimera_native_isa.py" assemble --arch riscv64 'ADDI x1,x2,5' >/dev/null

if [[ "$MODE" == "--check" ]]; then
  python3 "$ROOT/tools/isa/build_native_isa_catalog.py" --check
  python3 "$ROOT/tools/isa/run_native_isa_conformance.py" --strict --no-write
else
  python3 "$ROOT/tools/isa/build_native_isa_catalog.py"
  python3 "$ROOT/tools/isa/run_native_isa_conformance.py" --strict
fi
