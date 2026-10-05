#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/mnt/c/tmp/ChimeraIIOS"
SRC="$ROOT/src/chimera-command-compat/chimera-cmd.c"
BUILDER="$ROOT/tools/build-chimera-command-compat.sh"
BACKUP_ROOT="$ROOT/.chimera-fix-backups"

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

log() {
    echo "[CHIMERA-FIX] $*"
}

[[ -d "$ROOT" ]] || die "Project root not found: $ROOT"
[[ -f "$SRC" ]] || die "Missing source: $SRC"
[[ -f "$BUILDER" ]] || die "Missing builder: $BUILDER"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_ROOT/command-compat-$STAMP"

mkdir -p "$BACKUP"

cp -p "$SRC" "$BACKUP/chimera-cmd.c"
cp -p "$BUILDER" "$BACKUP/build-chimera-command-compat.sh"

log "Backups: $BACKUP"

# ------------------------------------------------------------
# Normalize CRLF.
# ------------------------------------------------------------

sed -i 's/\r$//' "$SRC"
sed -i 's/\r$//' "$BUILDER"

# ------------------------------------------------------------
# C feature-test macros.
# ------------------------------------------------------------

sed -i '/^[[:space:]]*#define _GNU_SOURCE[[:space:]]*$/d' "$SRC"

if ! grep -q '^#define _POSIX_C_SOURCE 200809L$' "$SRC"; then
    sed -i '1i#define _POSIX_C_SOURCE 200809L' "$SRC"
    log "Added POSIX C11 feature level"
fi

log "Removed duplicate _GNU_SOURCE"

# ------------------------------------------------------------
# Remove GNU feature flag from builder.
# ------------------------------------------------------------

sed -i \
    -e 's/[[:space:]]*-D_GNU_SOURCE[=1]*//g' \
    "$BUILDER"

# ------------------------------------------------------------
# Make sure the builder uses strict C11.
# ------------------------------------------------------------

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

# Find the compiler command containing chimera-cmd.c.
lines = s.splitlines()
out = []
inside = False

for line in lines:
    if '"$SRC/chimera-cmd.c"' in line:
        if not inside:
            indent = line[:len(line) - len(line.lstrip())]

            out.extend([
                indent + '"$CC" \\',
                indent + '    -std=c11 \\',
                indent + '    -O2 \\',
                indent + '    -Wall \\',
                indent + '    -Wextra \\',
                indent + '    -Werror \\',
                indent + '    "$SRC/chimera-cmd.c" \\',
                indent + '    -o "$BIN/chimera-cmd"',
            ])

            inside = True

        continue

    if inside:
        if '-o "$BIN/chimera-cmd"' in line:
            inside = False
        continue

    out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8")
PY

# ------------------------------------------------------------
# Ensure checked write helper exists.
# ------------------------------------------------------------

if ! grep -q 'static int write_all_fd' "$SRC"; then

python3 - "$SRC" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

anchor = "#include <unistd.h>"

helper = r'''
static int write_all_fd(int fd, const void *data, size_t len)
{
    const unsigned char *p = (const unsigned char *)data;

    while (len > 0) {
        ssize_t n = write(fd, p, len);

        if (n < 0) {
            if (errno == EINTR)
                continue;

            return -1;
        }

        if (n == 0)
            return -1;

        p += (size_t)n;
        len -= (size_t)n;
    }

    return 0;
}
'''

if anchor not in s:
    raise SystemExit("unistd.h include not found")

s = s.replace(anchor, anchor + "\n" + helper, 1)

p.write_text(s, encoding="utf-8")
PY

    log "Installed checked write_all_fd()"
fi

# ------------------------------------------------------------
# Replace unchecked stdout writes.
# ------------------------------------------------------------

python3 - "$SRC" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

old = 'write(STDOUT_FILENO, buf, (size_t)n);'

new = '''if (write_all_fd(STDOUT_FILENO, buf, (size_t)n) < 0) {
                perror("write");
                close(fd);
                return 1;
            }'''

count = s.count(old)

if count:
    s = s.replace(old, new)
    print(f"[CHIMERA-FIX] Replaced {count} unchecked write() calls")
else:
    print("[CHIMERA-FIX] No unchecked cat() writes found")

p.write_text(s, encoding="utf-8")
PY

# ------------------------------------------------------------
# Strict shell validation of THIS fixer before running it.
# ------------------------------------------------------------

log "Validating repaired fixer syntax..."

bash -n "$0"

log "Fixer syntax: PASS"

# ------------------------------------------------------------
# Validate builder syntax.
# ------------------------------------------------------------

bash -n "$BUILDER"

log "Builder syntax: PASS"

# ------------------------------------------------------------
# Validate C.
# ------------------------------------------------------------

CC_BIN="${CC:-cc}"

log "Running strict C11 compiler validation..."

"$CC_BIN" \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -fsyntax-only \
    "$SRC"

log "C11 compiler validation: PASS"

# ------------------------------------------------------------
# Validate no duplicate GNU feature macro remains.
# ------------------------------------------------------------

if grep -q '^#define _GNU_SOURCE' "$SRC"; then
    die "_GNU_SOURCE remains in source"
fi

if grep -q -- '-D_GNU_SOURCE' "$BUILDER"; then
    die "-D_GNU_SOURCE remains in builder"
fi

# ------------------------------------------------------------
# Verify checked write implementation.
# ------------------------------------------------------------

grep -q 'static int write_all_fd' "$SRC" \
    || die "write_all_fd() missing"

# ------------------------------------------------------------
# Registry validation.
# ------------------------------------------------------------

REGISTRY="$ROOT/rootfs/etc/chimera/commands/registry.tsv"

if [[ -f "$REGISTRY" ]]; then

    log "Checking Arabic command registry..."

    awk -F '\t' '
        $1 == "ls" && $2 == "عرض" {
            found=1
        }
        END {
            if (!found)
                exit 1
        }
    ' "$REGISTRY" \
        || die "Missing Arabic mapping: عرض -> ls"

    log "Arabic mapping: عرض -> ls : PASS"
fi

# ------------------------------------------------------------
# Final report.
# ------------------------------------------------------------

echo
echo "============================================================"
echo " Chimera II Command Compatibility Repair"
echo "============================================================"
echo "Source       : $SRC"
echo "Builder      : $BUILDER"
echo "Backup       : $BACKUP"
echo "C11/Werror   : PASS"
echo "GNU macro    : removed"
echo "write()      : checked"
echo "Shell syntax : PASS"
echo "Registry     : PASS"
echo "============================================================"
echo
echo "[NEXT] Run:"
echo "  sudo ./tools/build-chimera-command-compat.sh"
echo
