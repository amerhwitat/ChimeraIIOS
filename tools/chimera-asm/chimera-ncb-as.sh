#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 ]]; then echo "usage: chimera-ncb-as.sh input.asm output.ncb [word-bits] [isa-id]" >&2; exit 2; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$(realpath "$1")"; OUT="$(realpath -m "$2")"; WORD="${3:-8192}"; ISA="${4:-1}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"${CXX:-c++}" -std=c++20 -O2 "$ROOT/tools/chimera-asm/chimera-as.cpp" -o "$TMP/chimera-as"
"$TMP/chimera-as" "$SRC" "$TMP/text.bin"
python3 - "$TMP/manifest.json" "$TMP/text.bin" "$WORD" "$ISA" <<'PY'
import json,sys
manifest,code,word,isa=sys.argv[1:]
json.dump({"word_bits":int(word),"isa_id":int(isa),"entry_section":".text","stack_bytes":1048576,"heap_limit_bytes":1073741824,"sections":[{"name":".text","path":code,"flags":5,"alignment":16}]},open(manifest,"w"))
PY
PYTHONPATH="$ROOT/tools/binary" python3 "$ROOT/tools/binary/build_ncb.py" "$TMP/manifest.json" "$OUT"
echo "NCB1 image created: $OUT"
echo "NOTE: wraps the current 16-byte Chimera record stream; this is not a complete relocatable object ABI or kernel loader."
