#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="$ROOT/rootfs/etc/chimera/commands/registry.tsv"
BACKUP_DIR="$ROOT/.chimera-fix-backups/alias-resolution-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

log() {
    printf '[CHIMERA-ALIAS-FIX] %s\n' "$*"
}

die() {
    printf '[CHIMERA-ALIAS-FIX][ERROR] %s\n' "$*" >&2
    exit 1
}

log "Root: $ROOT"

[[ -f "$REGISTRY" ]] || die "Registry not found: $REGISTRY"

# ------------------------------------------------------------
# 1. Locate the actual chimera dispatcher source/generator.
# ------------------------------------------------------------

mapfile -t CANDIDATES < <(
    grep -RIl \
        --exclude-dir=.git \
        --exclude='*.o' \
        --exclude='*.elf' \
        --exclude='*.iso' \
        --exclude='*.img' \
        --exclude='*.bin' \
        --exclude='*.bak' \
        -E \
        'chimera-cmd|registry\.tsv|native command unavailable|native implementation' \
        "$ROOT/tools" "$ROOT/src" "$ROOT/scripts" "$ROOT/build" 2>/dev/null |
    sort -u
)

log "Potential dispatcher/build sources: ${#CANDIDATES[@]}"

for f in "${CANDIDATES[@]}"; do
    printf '  %s\n' "$f"
done

# Prefer shell generators that explicitly create /usr/bin/chimera.
SOURCE=""

for f in "${CANDIDATES[@]}"; do
    if [[ "$f" == *.sh ]] && grep -Eq \
        'usr/bin/chimera|DISPATCHER|chimera-cmd|registry.tsv' "$f"; then
        SOURCE="$f"
        break
    fi
done

# Fall back to any source containing the generated dispatcher logic.
if [[ -z "$SOURCE" ]]; then
    for f in "${CANDIDATES[@]}"; do
        if grep -Eq \
            'native command unavailable|registry\.tsv|chimera-cmd' "$f"; then
            SOURCE="$f"
            break
        fi
    done
fi

if [[ -z "$SOURCE" ]]; then
    log "No source generator found automatically."
    log "Searching generated rootfs dispatcher instead."

    if [[ -x "$ROOT/rootfs/usr/bin/chimera" ]]; then
        SOURCE="$ROOT/rootfs/usr/bin/chimera"
    else
        die "Could not locate either dispatcher source or generated dispatcher."
    fi
fi

log "Selected target: $SOURCE"

# ------------------------------------------------------------
# 2. Backup.
# ------------------------------------------------------------

BACKUP="$BACKUP_DIR/$(basename "$SOURCE")"

cp -a -- "$SOURCE" "$BACKUP"

log "Backup: $BACKUP"

# ------------------------------------------------------------
# 3. If this is a shell dispatcher, replace the resolver.
# ------------------------------------------------------------

if [[ "$SOURCE" == *.sh ]]; then

python3 - "$SOURCE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

# Look for a resolver function commonly used by the builder.
markers = (
    "native command unavailable",
    "registry.tsv",
    "CHIMERA_COMMAND_ROOT",
    "chimera-cmd",
)

if not any(x in s for x in markers):
    raise SystemExit(
        "Selected shell source does not contain recognizable dispatcher logic"
    )

# Insert a reusable registry resolver immediately before the first
# obvious dispatcher invocation if it does not already exist.
if "chimera_resolve_command()" not in s:

    resolver = r'''
chimera_resolve_command() {
    local requested="${1:-}"
    local registry="${CHIMERA_REGISTRY:-/etc/chimera/commands/registry.tsv}"
    local canonical alias implementation target source

    [[ -n "$requested" ]] || return 1
    [[ -r "$registry" ]] || return 1

    # Exact canonical command match.
    while IFS=$'\t' read -r canonical alias implementation target source _; do
        [[ -n "$canonical" ]] || continue
        [[ "$canonical" == \#* ]] && continue

        if [[ "$requested" == "$canonical" ]]; then
            printf '%s\t%s\t%s\t%s\n' \
                "$canonical" "$implementation" "$target" "$source"
            return 0
        fi
    done < "$registry"

    # Arabic/alternate alias match.
    while IFS=$'\t' read -r canonical alias implementation target source _; do
        [[ -n "$canonical" ]] || continue
        [[ "$canonical" == \#* ]] && continue
        [[ -n "$alias" ]] || continue

        if [[ "$requested" == "$alias" ]]; then
            printf '%s\t%s\t%s\t%s\n' \
                "$canonical" "$implementation" "$target" "$source"
            return 0
        fi
    done < "$registry"

    return 1
}

'''

    # Put resolver near the beginning after the first set/shebang area.
    lines = s.splitlines(True)
    insert_at = 1 if lines and lines[0].startswith("#!") else 0

    lines.insert(insert_at, resolver)
    s = "".join(lines)

# Replace common direct native dispatch forms.
s = s.replace(
    '"$NATIVE" "$1" "${@:2}"',
    '"$NATIVE" "$CANONICAL" "${@:2}"'
)

s = s.replace(
    '"$NATIVE" "$COMMAND" "${ARGS[@]}"',
    '"$NATIVE" "$CANONICAL" "${ARGS[@]}"'
)

p.write_text(s)
PY

chmod +x "$SOURCE"

# If this is already the generated dispatcher, patch it directly below.
else

python3 - "$SOURCE" "$REGISTRY" <<'PY'
from pathlib import Path
import sys

dispatcher = Path(sys.argv[1])
registry = Path(sys.argv[2])

s = dispatcher.read_text()

if "chimera_resolve_command()" in s:
    print("[CHIMERA-ALIAS-FIX] Resolver already present.")
    raise SystemExit(0)

resolver = r'''
chimera_resolve_command() {
    local requested="${1:-}"
    local registry="${CHIMERA_REGISTRY:-/etc/chimera/commands/registry.tsv}"
    local canonical alias implementation target source

    [[ -n "$requested" ]] || return 1
    [[ -r "$registry" ]] || return 1

    while IFS=$'\t' read -r canonical alias implementation target source _; do
        [[ -n "$canonical" ]] || continue
        [[ "$canonical" == \#* ]] && continue

        if [[ "$requested" == "$canonical" ||
              ( -n "$alias" && "$requested" == "$alias" ) ]]; then
            printf '%s\t%s\t%s\t%s\n' \
                "$canonical" "$implementation" "$target" "$source"
            return 0
        fi
    done < "$registry"

    return 1
}

'''

lines = s.splitlines(True)
insert_at = 1 if lines and lines[0].startswith("#!") else 0
lines.insert(insert_at, resolver)
s = "".join(lines)

dispatcher.write_text(s)
PY

chmod +x "$SOURCE"

fi

# ------------------------------------------------------------
# 4. Validate registry mappings.
# ------------------------------------------------------------

log "Checking registry..."

grep -q $'^ls\tعرض\t' "$REGISTRY" \
    || die "Missing ls -> عرض registry mapping"

grep -q $'^cat\tاقرأ\t' "$REGISTRY" \
    || die "Missing cat -> اقرأ registry mapping"

log "Registry Arabic mappings: PASS"

# ------------------------------------------------------------
# 5. Rebuild command compatibility layer.
# ------------------------------------------------------------

BUILDER="$ROOT/tools/build-chimera-command-compat.sh"

if [[ -x "$BUILDER" || -f "$BUILDER" ]]; then
    log "Rebuilding command compatibility layer..."

    bash "$BUILDER"
else
    log "Builder not found; using existing dispatcher."
fi

# ------------------------------------------------------------
# 6. Verify generated dispatcher.
# ------------------------------------------------------------

DISPATCHER="$ROOT/rootfs/usr/bin/chimera"

[[ -x "$DISPATCHER" ]] || die \
    "Generated dispatcher missing after repair: $DISPATCHER"

log "Generated dispatcher: $DISPATCHER"

# Verify the resolver survived generation.
if ! grep -q 'registry.tsv' "$DISPATCHER"; then
    log "WARNING: generated dispatcher does not visibly reference registry.tsv."
fi

# ------------------------------------------------------------
# 7. Functional tests.
# ------------------------------------------------------------

log "Testing canonical ls..."

LS_OUTPUT="$("$DISPATCHER" ls "$ROOT" 2>&1)" || {
    printf '%s\n' "$LS_OUTPUT"
    die "Canonical ls failed"
}

log "Canonical ls: PASS"

log "Testing Arabic عرض -> ls..."

AR_OUTPUT="$("$DISPATCHER" عرض "$ROOT" 2>&1)" || {
    printf '%s\n' "$AR_OUTPUT"
    die "Arabic alias عرض -> ls failed"
}

log "عرض -> ls: PASS"

log "Testing canonical cat..."

TESTFILE="$(mktemp)"
trap 'rm -f "$TESTFILE"' EXIT

printf 'CHIMERA_CAT_OK\n' > "$TESTFILE"

CAT_OUTPUT="$("$DISPATCHER" cat "$TESTFILE" 2>&1)" || {
    printf '%s\n' "$CAT_OUTPUT"
    die "Canonical cat failed"
}

[[ "$CAT_OUTPUT" == "CHIMERA_CAT_OK" ]] || {
    printf '%s\n' "$CAT_OUTPUT"
    die "Canonical cat returned unexpected output"
}

log "Canonical cat: PASS"

log "Testing Arabic اقرأ -> cat..."

ARCAT_OUTPUT="$("$DISPATCHER" اقرأ "$TESTFILE" 2>&1)" || {
    printf '%s\n' "$ARCAT_OUTPUT"
    die "Arabic alias اقرأ -> cat failed"
}

[[ "$ARCAT_OUTPUT" == "CHIMERA_CAT_OK" ]] || {
    printf '%s\n' "$ARCAT_OUTPUT"
    die "Arabic cat returned unexpected output"
}

log "اقرأ -> cat: PASS"

echo
echo "============================================================"
echo " Chimera II Arabic Command Resolution"
echo "============================================================"
echo "Dispatcher       : $DISPATCHER"
echo "Registry          : $REGISTRY"
echo "Canonical ls      : PASS"
echo "عرض -> ls         : PASS"
echo "Canonical cat     : PASS"
echo "اقرأ -> cat       : PASS"
echo "Registry          : PASS"
echo "============================================================"
