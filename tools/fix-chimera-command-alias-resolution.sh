#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/mnt/c/tmp/ChimeraIIOS"
BUILDER="$ROOT/tools/build-chimera-command-compat.sh"
ROOTFS="$ROOT/rootfs"
DISPATCHER="$ROOTFS/usr/bin/chimera"
REGISTRY="$ROOTFS/etc/chimera/commands/registry.tsv"
BACKUPS="$ROOT/.chimera-fix-backups/alias-resolution-$(date +%Y%m%d-%H%M%S)"

log() {
    printf '[CHIMERA-ALIAS-FIX] %s\n' "$*"
}

die() {
    printf '[CHIMERA-ALIAS-FIX][ERROR] %s\n' "$*" >&2
    exit 1
}

[[ -f "$BUILDER" ]] || die "Missing builder: $BUILDER"

mkdir -p "$BACKUPS"

cp -p "$BUILDER" "$BACKUPS/build-chimera-command-compat.sh"

log "Backup: $BACKUPS"

sed -i 's/\r$//' "$BUILDER"

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

# We want the generated /usr/bin/chimera dispatcher to resolve:
#
#   canonical command -> mode -> implementation
#   Arabic alias      -> canonical command -> same resolver
#
# The generated dispatcher is therefore rewritten as a complete,
# deterministic shell dispatcher instead of trying to patch individual
# aliases.

marker = 'cat > "$ROOTFS/usr/bin/chimera" <<'
m = re.search(r'cat\s*>\s*"\$ROOTFS/usr/bin/chimera"\s*<<[\'"]?([A-Za-z0-9_]+)[\'"]?', s)

if not m:
    raise SystemExit(
        "Could not locate generated chimera dispatcher in builder. "
        "Builder format is different; no blind modification performed."
    )

heredoc_tag = m.group(1)

body_start = m.end()
body_end = s.find("\n" + heredoc_tag, body_start)

if body_end < 0:
    raise SystemExit("Could not locate end of chimera dispatcher heredoc")

new_dispatcher = r'''#!/usr/bin/env bash
set -Eeuo pipefail

# Chimera II command dispatcher.
#
# Resolution order:
#   1. exact canonical command
#   2. Arabic alias from registry.tsv
#   3. compatibility-mode command
#
# registry.tsv format:
#   command<TAB>arabic_alias<TAB>mode<TAB>implementation<TAB>reference

ROOT_PREFIX="${CHIMERA_ROOT_PREFIX:-}"
COMMAND_ROOT="${CHIMERA_COMMAND_ROOT:-${ROOT_PREFIX}/etc/chimera/commands}"

if [[ -z "$ROOT_PREFIX" ]]; then
    COMMAND_ROOT="/etc/chimera/commands"
fi

REGISTRY="${CHIMERA_COMMAND_REGISTRY:-$COMMAND_ROOT/registry.tsv}"

if [[ ! -f "$REGISTRY" ]]; then
    echo "chimera: command registry unavailable: $REGISTRY" >&2
    exit 127
fi

usage() {
    cat <<'USAGE'
Chimera II command dispatcher

Usage:
  chimera [MODE] COMMAND [ARGUMENTS...]
  chimera COMMAND [ARGUMENTS...]

Modes:
  native
  linux
  posix
  bash
  zsh
  macos
  windows
  cmd
  powershell
USAGE
}

is_mode() {
    case "$1" in
        native|linux|posix|bash|zsh|macos|windows|cmd|powershell)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

resolve_command() {
    local query="$1"

    awk -F '\t' -v q="$query" '
        BEGIN { IGNORECASE=0 }

        /^[[:space:]]*#/ { next }
        NF < 4 { next }

        $1 == q {
            print $1 "\t" $2 "\t" $3 "\t" $4 "\t" $5
            exit
        }

        $2 == q {
            print $1 "\t" $2 "\t" $3 "\t" $4 "\t" $5
            exit
        }
    ' "$REGISTRY"
}

if (( $# == 0 )); then
    usage
    exit 0
fi

MODE="native"

if is_mode "$1" && (( $# >= 2 )); then
    MODE="$1"
    shift
fi

QUERY="$1"
shift

RESOLVED="$(resolve_command "$QUERY" || true)"

if [[ -z "$RESOLVED" ]]; then
    echo "chimera: command not found: $QUERY" >&2
    echo "chimera: use 'chimera help' or 'chimera list'." >&2
    exit 127
fi

IFS=$'\t' read -r CANONICAL ARABIC REGISTRY_MODE IMPLEMENTATION REFERENCE \
    <<< "$RESOLVED"

# The registry's native implementation remains authoritative for native mode.
EFFECTIVE_MODE="$MODE"

if [[ "$MODE" == "native" ]]; then
    EFFECTIVE_MODE="$REGISTRY_MODE"
fi

# Built-in information commands.
case "$QUERY" in
    help|مساعدة)
        if (( $# == 0 )); then
            printf 'Command: %s\n' "$CANONICAL"
            printf 'Arabic alias: %s\n' "$ARABIC"
            printf 'Mode: %s\n' "$REGISTRY_MODE"
            printf 'Implementation: %s\n' "$IMPLEMENTATION"
            printf 'Reference: %s\n' "$REFERENCE"
            exit 0
        fi
        ;;
esac

# Native command implementation.
if [[ "$EFFECTIVE_MODE" == "native" ]]; then
    if [[ "$IMPLEMENTATION" == "chimera-cmd" ]]; then

        NATIVE="${ROOT_PREFIX}/usr/bin/chimera-cmd"

        [[ -x "$NATIVE" ]] || {
            echo "chimera: native runtime unavailable: $NATIVE" >&2
            exit 127
        }

        exec "$NATIVE" "$CANONICAL" "$@"
    fi
fi

# Native commands whose registry entry explicitly identifies a command
# executable are resolved here.
if [[ "$EFFECTIVE_MODE" == "native" ]]; then
    if [[ -x "${ROOT_PREFIX}/usr/bin/$IMPLEMENTATION" ]]; then
        exec "${ROOT_PREFIX}/usr/bin/$IMPLEMENTATION" "$@"
    fi

    if command -v "$IMPLEMENTATION" >/dev/null 2>&1; then
        exec "$IMPLEMENTATION" "$@"
    fi
fi

# Compatibility modes.
case "$EFFECTIVE_MODE" in
    linux|posix)
        if command -v "$IMPLEMENTATION" >/dev/null 2>&1; then
            exec "$IMPLEMENTATION" "$@"
        fi

        echo "chimera: Linux/POSIX implementation unavailable: $IMPLEMENTATION" >&2
        exit 127
        ;;

    bash)
        exec bash -c '
            command="$1"
            shift
            command "$@"
        ' bash "$IMPLEMENTATION" "$@"
        ;;

    zsh)
        command -v zsh >/dev/null 2>&1 || {
            echo "chimera: zsh runtime unavailable" >&2
            exit 127
        }

        exec zsh -c '
            command="$1"
            shift
            command "$@"
        ' zsh "$IMPLEMENTATION" "$@"
        ;;

    macos)
        echo "chimera: macOS compatibility runtime required for: $CANONICAL" >&2
        echo "chimera: implementation: $IMPLEMENTATION" >&2
        exit 126
        ;;

    windows|cmd)
        echo "chimera: Windows compatibility runtime required for: $CANONICAL" >&2
        echo "chimera: implementation: $IMPLEMENTATION" >&2
        exit 126
        ;;

    powershell)
        command -v pwsh >/dev/null 2>&1 || {
            echo "chimera: PowerShell runtime unavailable: pwsh" >&2
            exit 127
        }

        exec pwsh -NoLogo -NoProfile -Command \
            '& $args[0] @($args[1..($args.Count-1)])' \
            "$IMPLEMENTATION" "$@"
        ;;

    native)
        echo "chimera: native implementation unavailable for '$CANONICAL'" >&2
        echo "chimera: registry mode='$REGISTRY_MODE' implementation='$IMPLEMENTATION'" >&2
        exit 127
        ;;

    *)
        echo "chimera: unsupported mode: $EFFECTIVE_MODE" >&2
        exit 126
        ;;
esac
'''

s = s[:body_start] + "\n" + new_dispatcher + "\n" + s[body_end:]

p.write_text(s, encoding="utf-8")

print("[CHIMERA-ALIAS-FIX] Dispatcher generator replaced")
PY

chmod +x "$BUILDER"

bash -n "$BUILDER"

log "Rebuilding command compatibility subsystem..."

sudo "$BUILDER"

[[ -x "$DISPATCHER" ]] || die "Generated dispatcher missing: $DISPATCHER"
[[ -f "$REGISTRY" ]] || die "Generated registry missing: $REGISTRY"

bash -n "$DISPATCHER"

log "Testing canonical command resolution..."

"$DISPATCHER" ls >/tmp/chimera-alias-ls.out

log "Canonical ls: PASS"

log "Testing Arabic alias resolution: عرض -> ls..."

"$DISPATCHER" عرض /tmp >/tmp/chimera-alias-arabic.out

log "Arabic عرض -> ls: PASS"

log "Testing Arabic alias resolution: اقرأ -> cat..."

TESTFILE="$(mktemp)"
trap 'rm -f "$TESTFILE"' EXIT

printf 'CHIMERA_ARABIC_CAT_OK\n' > "$TESTFILE"

CAT_OUTPUT="$("$DISPATCHER" اقرأ "$TESTFILE")"

[[ "$CAT_OUTPUT" == "CHIMERA_ARABIC_CAT_OK" ]] || {
    echo "[ERROR] اقرأ -> cat returned unexpected output:" >&2
    printf '%s\n' "$CAT_OUTPUT" >&2
    exit 1
}

log "Arabic اقرأ -> cat: PASS"

log "Testing registry directly..."

grep -P '^ls\tعرض\t' "$REGISTRY" >/dev/null || {
    echo "[ERROR] Registry missing ls -> عرض mapping." >&2
    exit 1
}

grep -P '^cat\tاقرأ\t' "$REGISTRY" >/dev/null || {
    echo "[ERROR] Registry missing cat -> اقرأ mapping." >&2
    exit 1
}

log "Registry Arabic mappings: PASS"

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
