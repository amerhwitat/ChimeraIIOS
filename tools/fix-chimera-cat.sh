#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/mnt/c/tmp/ChimeraIIOS"
SRC="$ROOT/src/chimera-command-compat/chimera-cmd.c"
BACKUP_ROOT="$ROOT/.chimera-fix-backups"

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

log() {
    echo "[CHIMERA-CAT-FIX] $*"
}

[[ -f "$SRC" ]] || die "Missing source: $SRC"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_ROOT/cat-fix-$STAMP"

mkdir -p "$BACKUP"
cp -p "$SRC" "$BACKUP/chimera-cmd.c"

log "Backup: $BACKUP/chimera-cmd.c"

sed -i 's/\r$//' "$SRC"

python3 - "$SRC" <<'PY'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

m = re.search(r'\bstatic\s+int\s+cmd_cat\s*\([^)]*\)\s*\{', s)

if not m:
    raise SystemExit("cmd_cat() was not found")

start = m.start()
brace = s.find("{", m.start())

depth = 0
end = None

for i in range(brace, len(s)):
    if s[i] == "{":
        depth += 1
    elif s[i] == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    raise SystemExit("Could not determine end of cmd_cat()")

new = r'''static int cmd_cat(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: cat FILE...\n");
        return 1;
    }

    for (int i = 1; i < argc; ++i) {
        int input_fd = open(argv[i], O_RDONLY);

        if (input_fd < 0) {
            fprintf(stderr,
                    "cat: %s: %s\n",
                    argv[i],
                    strerror(errno));
            return 1;
        }

        unsigned char buf[8192];

        for (;;) {
            ssize_t n = read(input_fd, buf, sizeof(buf));

            if (n < 0) {
                if (errno == EINTR)
                    continue;

                fprintf(stderr,
                        "cat: %s: %s\n",
                        argv[i],
                        strerror(errno));

                close(input_fd);
                return 1;
            }

            if (n == 0)
                break;

            if (write_all_fd(STDOUT_FILENO,
                             buf,
                             (size_t)n) < 0) {
                fprintf(stderr,
                        "cat: write: %s\n",
                        strerror(errno));

                close(input_fd);
                return 1;
            }
        }

        if (close(input_fd) < 0) {
            fprintf(stderr,
                    "cat: %s: %s\n",
                    argv[i],
                    strerror(errno));
            return 1;
        }
    }

    return 0;
}'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")

print("[CHIMERA-CAT-FIX] cmd_cat() normalized")
PY

bash -n tools/fix-chimera-cat.sh

CC_BIN="${CC:-cc}"

echo
echo "[CHIMERA-CAT-FIX] Running strict C11 compiler validation..."

"$CC_BIN" \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -fsyntax-only \
    "$SRC"

echo "[CHIMERA-CAT-FIX] Strict C11 validation: PASS"

TMP="$(mktemp)"
TESTFILE="$(mktemp)"

cleanup() {
    rm -f -- "$TMP" "$TESTFILE"
}
trap cleanup EXIT

echo
echo "[CHIMERA-CAT-FIX] Building isolated native runtime..."

"$CC_BIN" \
    -std=c11 \
    -O2 \
    -Wall \
    -Wextra \
    -Werror \
    "$SRC" \
    -o "$TMP"

echo "[CHIMERA-CAT-FIX] Native runtime compilation: PASS"

printf 'CHIMERA_CAT_TEST_OK\n' > "$TESTFILE"

echo
echo "[CHIMERA-CAT-FIX] Testing native cat implementation..."

# chimera-cmd is a multicall binary whose native command
# dispatcher resolves the command from argv[0].
#
# Therefore test it exactly as the installed native command
# links are used: create a temporary "cat" symlink.

TEST_BIN_DIR="$(mktemp -d)"

cleanup() {
    rm -rf -- "$TEST_BIN_DIR"
    rm -f -- "$TMP" "$TESTFILE"
}
trap cleanup EXIT

ln -s -- "$TMP" "$TEST_BIN_DIR/cat"

OUTPUT="$("$TEST_BIN_DIR/cat" "$TESTFILE")"

if [[ "$OUTPUT" != "CHIMERA_CAT_TEST_OK" ]]; then
    echo "[ERROR] Native cat test failed." >&2
    echo "Expected: CHIMERA_CAT_TEST_OK" >&2
    echo "Received : $OUTPUT" >&2
    echo "Executable: $TMP" >&2
    echo "Dispatcher link: $TEST_BIN_DIR/cat" >&2
    exit 1
fi

echo "[CHIMERA-CAT-FIX] Native cat test: PASS"

echo
echo "[CHIMERA-CAT-FIX] Testing command dispatch semantics..."

HELP_OUTPUT="$("$TMP" help 2>&1 || true)"

if [[ -z "$HELP_OUTPUT" ]]; then
    echo "[CHIMERA-CAT-FIX] Dispatcher help returned no output; continuing."
else
    echo "[CHIMERA-CAT-FIX] Dispatcher responds: PASS"
fi

echo
echo "[CHIMERA-CAT-FIX] Checking source for stale fd reference..."

if python3 - "$SRC" <<'PY'
from pathlib import Path
import re
import sys

s = Path(sys.argv[1]).read_text(encoding="utf-8")

m = re.search(r'\bstatic\s+int\s+cmd_cat\s*\([^)]*\)\s*\{', s)

if not m:
    raise SystemExit(1)

brace = s.find("{", m.start())
depth = 0
end = None

for i in range(brace, len(s)):
    if s[i] == "{":
        depth += 1
    elif s[i] == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

body = s[m.start():end]

# A bare fd reference inside cmd_cat is no longer permitted.
# input_fd is the descriptor owned by this function.
if re.search(r'\bclose\s*\(\s*fd\s*\)', body):
    raise SystemExit(1)

if "input_fd" not in body:
    raise SystemExit(1)
PY
then
    echo "[CHIMERA-CAT-FIX] Descriptor validation: PASS"
else
    die "Stale fd reference detected in cmd_cat()"
fi

echo
echo "============================================================"
echo " Chimera II OS — cat() Repair"
echo "============================================================"
echo "Source          : $SRC"
echo "Backup          : $BACKUP"
echo "Strict C11      : PASS"
echo "Werror          : PASS"
echo "Native compile  : PASS"
echo "Native cat()    : PASS"
echo "Descriptor      : input_fd"
echo "Stale fd bug    : FIXED"
echo "============================================================"
echo
echo "[NEXT] Rebuild the complete command compatibility subsystem:"
echo
echo "  sudo ./tools/build-chimera-command-compat.sh"
echo
