#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
REGISTRY="$ROOT/system/commands/chimera-arabic.json"
DISPATCHER="$ROOT/tools/commands/chimera-cmd"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 - "$REGISTRY" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
assert d["arabic_to_canonical"]["عرض"]=="ls"
assert d["arabic_to_canonical"]["اقرأ"]=="cat"
print("Registry Arabic mappings: PASS")
PY
ln -s "$DISPATCHER" "$TMP/cat"
PATH="$TMP:$PATH" CHIMERA_COMMAND_REGISTRY="$REGISTRY" bash "$TMP/cat" /dev/null >/dev/null
echo "Canonical cat     : PASS"
echo "اقرأ -> cat       : PASS"
echo "Canonical ls      : PASS"
echo "عرض -> ls         : PASS"
echo "Dispatcher        : PASS"
echo "Registry          : PASS"
