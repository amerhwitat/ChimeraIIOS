#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${CHIMERA_CMD_SOURCE:-$ROOT/src/chimera-command-compat/chimera-cmd.c}"
OUT="${CHIMERA_CMD_OUT:-$ROOT/build/command-arch-matrix}"
CC_BIN="${CC:-cc}"
ARCH="${TARGET_ARCH:-$(uname -m)}"
test -s "$SOURCE" || { echo "missing command source: $SOURCE" >&2; exit 2; }
command -v "$CC_BIN" >/dev/null 2>&1 || { echo "missing compiler: $CC_BIN" >&2; exit 127; }
mkdir -p "$OUT/$ARCH"
"$CC_BIN" -std=c11 -O2 -Wall -Wextra -Werror "$SOURCE" -o "$OUT/$ARCH/chimera-cmd"
chmod 0755 "$OUT/$ARCH/chimera-cmd"
if command -v readelf >/dev/null 2>&1; then readelf -h "$OUT/$ARCH/chimera-cmd" > "$OUT/$ARCH/elf-header.txt"; fi
sha256sum "$OUT/$ARCH/chimera-cmd" > "$OUT/$ARCH/SHA256SUMS"
printf "Built %s command multicall binary for %s; ABI/runtime validation remains a separate gate.\n" "$OUT/$ARCH/chimera-cmd" "$ARCH"
