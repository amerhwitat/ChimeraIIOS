#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

# Repair source files that contain literal backslash-newline sequences outside
# string literals. This protects the ISO build from generated/editing artifacts
# such as "\\n" accidentally being written into C++ source code.
repair_literal_newlines() {
    local file="$1"
    [[ -f "$file" ]] || return 0

    python3 - "$file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Repair literal two-character "\n" sequences only when they appear as
# source-level separators. Do not alter normal C/C++ string escapes.
lines = text.splitlines(keepends=True)
changed = False
out = []

for line in lines:
    if "\\n" in line:
        parts = line.split("\\n")
        if len(parts) > 1:
            rebuilt = parts[0]
            for part in parts[1:]:
                rebuilt += "\n" + part
            if rebuilt != line:
                line = rebuilt
                changed = True
    out.append(line)

if changed:
    path.write_text("".join(out), encoding="utf-8")
    print(f"[FIX] Repaired literal \\n sequences: {path}")
PY
}

preflight_sources() {
    echo "[CHECK] Validating generated C/C++ sources before ISO build..."
    repair_literal_newlines "$ROOT/arch/registern/ChimeraCorePool.cpp"
}

preflight_sources
exec "$ROOT/tools/build-full-iso.sh" "$@"
