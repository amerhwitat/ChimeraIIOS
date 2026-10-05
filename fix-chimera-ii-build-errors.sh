#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/mnt/c/tmp/ChimeraIIOS"
FOREIGN="$ROOT/tools/fetch-foreign-runtimes.sh"
LIVE="$ROOT/tools/build-live-boot-binaries.sh"
BACKUP_DIR="$ROOT/.chimera-fix-backups"

echo "[CHIMERA FIX] Root: $ROOT"

[[ -d "$ROOT" ]] || {
    echo "[ERROR] Project not found: $ROOT" >&2
    exit 1
}

[[ -f "$FOREIGN" ]] || {
    echo "[ERROR] Missing: $FOREIGN" >&2
    exit 1
}

mkdir -p "$BACKUP_DIR"

backup_once() {
    local src="$1"
    local name
    local dst

    name="$(basename -- "$src")"
    dst="$BACKUP_DIR/${name}.before-auto-fix"

    if [[ ! -e "$dst" ]]; then
        cp -p -- "$src" "$dst"
        echo "[BACKUP] $dst"
    else
        echo "[BACKUP] Existing: $dst"
    fi
}

backup_once "$FOREIGN"

if [[ -f "$LIVE" ]]; then
    backup_once "$LIVE"
fi

# ------------------------------------------------------------
# FIX 1: Repair literal \n corruption in fetch-foreign-runtimes.sh
# ------------------------------------------------------------

echo "[FIX 1] Repairing fetch-foreign-runtimes.sh..."

python3 - "$FOREIGN" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

needle = '    if apt-cache show "$p" >/dev/null 2>&1; then'
start = s.find(needle)

if start < 0:
    print("[ERROR] Could not find apt-cache block.")
    sys.exit(2)

end = s.find("    fi", start)

if end < 0:
    print("[ERROR] Could not find end of apt-cache block.")
    sys.exit(3)

end += len("    fi")

block = s[start:end]

if r"\n" in block:
    block = block.replace(r"\n", "\n")
    s = s[:start] + block + s[end:]
    p.write_text(s)
    print("[FIX] Converted literal \\n sequences to real newlines.")
else:
    print("[OK] apt-cache block already uses real newlines.")
PY

echo "[CHECK] fetch-foreign-runtimes.sh..."

if ! bash -n "$FOREIGN"; then
    echo "[ERROR] fetch-foreign-runtimes.sh still has syntax errors." >&2
    echo
    echo "----- lines 42-55 -----"
    nl -ba "$FOREIGN" | sed -n '42,55p'
    echo "-----------------------"
    exit 2
fi

echo "[OK] fetch-foreign-runtimes.sh syntax is valid."

# ------------------------------------------------------------
# FIX 2: Protect Koronos copy from source == destination
# ------------------------------------------------------------

if [[ -f "$LIVE" ]]; then

    echo "[FIX 2] Protecting Koronos self-copy..."

    python3 - "$LIVE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

helper = r'''chimera_copy_if_distinct() {
    local src="$1"
    local dst="$2"

    [[ -e "$src" ]] || {
        echo "[ERROR] Copy source missing: $src" >&2
        return 2
    }

    mkdir -p "$(dirname "$dst")"

    local src_real
    local dst_real

    src_real="$(realpath -m -- "$src")"
    dst_real="$(realpath -m -- "$dst")"

    if [[ "$src_real" == "$dst_real" ]]; then
        echo "[CHIMERA] SKIP self-copy: $src_real"
        return 0
    fi

    cp -f -- "$src" "$dst"
}
'''

if "chimera_copy_if_distinct()" not in s:
    marker = "set -Eeuo pipefail"

    if marker in s:
        s = s.replace(
            marker,
            marker + "\n\n" + helper,
            1
        )
    else:
        s = helper + "\n" + s

old = 'cp -f "$KORONOS" "$OUT/boot/koronos/koronos.elf"'
new = 'chimera_copy_if_distinct "$KORONOS" "$OUT/boot/koronos/koronos.elf"'

s = s.replace(old, new, 1)

s = s.replace(
    '$OUT/boot/koronos/koronos.el.sha256',
    '$OUT/boot/koronos/koronos.elf.sha256'
)

p.write_text(s)

print("[FIX] Koronos protection installed.")
PY

    if ! bash -n "$LIVE"; then
        echo "[ERROR] $LIVE still has syntax errors." >&2
        exit 3
    fi

    echo "[OK] build-live-boot-binaries.sh syntax is valid."
fi

# ------------------------------------------------------------
# FIX 3: Validate active scripts
# ------------------------------------------------------------

echo "[CHECK] Validating active shell scripts..."

BAD=0

while IFS= read -r -d '' file; do

    case "$file" in
        *.pre-docker-log-fix)
            continue
            ;;
        */.chimera-fix-backups/*)
            continue
            ;;
        */fix-chimera-ii-boot-artifacts.sh)
            continue
            ;;
    esac

    if ! bash -n "$file"; then
        echo "[ERROR] Syntax error: $file"
        BAD=1
    fi

done < <(
    find "$ROOT" \
        -type f \
        -name "*.sh" \
        -print0 2>/dev/null
)

if (( BAD != 0 )); then
    echo
    echo "[ERROR] Active shell scripts still contain syntax errors."
    exit 4
fi

echo
echo "============================================================"
echo "[SUCCESS] Chimera II build scripts repaired."
echo "============================================================"
echo
echo "Backups:"
echo "  $BACKUP_DIR"
echo
echo "Next:"
echo "  Run your normal Chimera II build command."
