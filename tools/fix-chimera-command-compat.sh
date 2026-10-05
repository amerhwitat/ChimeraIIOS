#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILDER="$ROOT/tools/build-chimera-command-compat.sh"
SOURCE="$ROOT/src/chimera-command-compat/chimera-cmd.c"
BACKUP="$ROOT/.chimera-fix-backups/command-compat-repair"

mkdir -p "$BACKUP"

backup_once() {
    local src="$1"
    local name
    local dst

    name="$(basename -- "$src")"
    dst="$BACKUP/${name}.before-repair"

    if [[ ! -e "$dst" ]]; then
        cp -p -- "$src" "$dst"
        echo "[BACKUP] $dst"
    fi
}

backup_once "$BUILDER"
[[ -f "$SOURCE" ]] && backup_once "$SOURCE"

###############################################################################
# 1. Remove duplicate _GNU_SOURCE definition
###############################################################################

python3 - "$SOURCE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

s = s.replace(
    "#define _GNU_SOURCE\n\n",
    ""
)

p.write_text(s)
PY

###############################################################################
# 2. Replace unsafe ignored write() calls with write_all()
###############################################################################

python3 - "$SOURCE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

marker = """static int cmd_pwd(void)
"""

helper = r'''static int write_all_fd(int fd, const void *data, size_t len)
{
    const char *p = (const char *)data;

    while (len > 0) {
        ssize_t n = write(fd, p, len);

        if (n < 0) {
            if (errno == EINTR)
                continue;

            return -1;
        }

        if (n == 0)
            return -1;

        p += n;
        len -= (size_t)n;
    }

    return 0;
}

'''

if "static int write_all_fd(" not in s:
    pos = s.find(marker)

    if pos < 0:
        raise SystemExit("Could not locate cmd_pwd() insertion point")

    s = s[:pos] + helper + s[pos:]

s = s.replace(
    """            write(STDOUT_FILENO, buf, (size_t)n);
""",
    """            if (write_all_fd(STDOUT_FILENO, buf, (size_t)n) < 0) {
                perror("cat");
                return 1;
            }
"""
)

p.write_text(s)
PY

###############################################################################
# 3. Make dispatcher understand staged rootfs
###############################################################################

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

old = r'''cat > "$BIN/chimera" <<'DISPATCH'
#!/usr/bin/env bash
set -euo pipefail

CONF="/etc/chimera/commands"
REGISTRY="$CONF/registry.tsv"
'''

new = r'''cat > "$BIN/chimera" <<'DISPATCH'
#!/usr/bin/env bash
set -euo pipefail

# CHIMERA_COMMAND_ROOT may point to the staged rootfs during build tests.
# Installed systems normally use /etc/chimera/commands.
CONF="${CHIMERA_COMMAND_ROOT:-/etc/chimera/commands}"
REGISTRY="$CONF/registry.tsv"
'''

if old not in s:
    raise SystemExit(
        "Could not locate dispatcher configuration block"
    )

s = s.replace(old, new)

p.write_text(s)
PY

###############################################################################
# 4. Fix dispatcher native executable root during staged testing
###############################################################################

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

old = r'''            if [[ -x "/usr/bin/$command" ]]; then
                exec "/usr/bin/$command" "$@"
            fi

            if command -v "$command" >/dev/null 2>&1; then
                exec "$command" "$@"
            fi
'''

new = r'''            local root_prefix="${CHIMERA_ROOT_PREFIX:-}"

            if [[ -x "${root_prefix}/usr/bin/$command" ]]; then
                exec "${root_prefix}/usr/bin/$command" "$@"
            fi

            if command -v "$command" >/dev/null 2>&1; then
                exec "$command" "$@"
            fi
'''

if old not in s:
    raise SystemExit(
        "Could not locate run_native() executable block"
    )

s = s.replace(old, new)

p.write_text(s)
PY

###############################################################################
# 5. Improve validation in builder
###############################################################################

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

old = r'''log "Testing command dispatcher..."

"$BIN/chimera" help ls
"$BIN/chimera" help عرض
'''

new = r'''log "Testing command dispatcher against staged rootfs..."

CHIMERA_COMMAND_ROOT="$CMDROOT" \
CHIMERA_ROOT_PREFIX="$OUT" \
    "$BIN/chimera" help ls

CHIMERA_COMMAND_ROOT="$CMDROOT" \
CHIMERA_ROOT_PREFIX="$OUT" \
    "$BIN/chimera" help عرض

###############################################################################
# Verify registry resolution
###############################################################################

log "Verifying registry resolution..."

registry_mode="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help ls |
        awk -F': ' '/^Mode:/ {print $2}'
)"

registry_impl="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help ls |
        awk -F': ' '/^Implementation:/ {print $2}'
)"

[[ -n "$registry_mode" ]] || {
    die "Registry mode lookup returned empty result."
}

[[ -n "$registry_impl" ]] || {
    die "Registry implementation lookup returned empty result."
}

[[ "$registry_mode" == "native" ]] || {
    die "ls must resolve to native mode, got: $registry_mode"
}

log "Registry resolution: ls -> $registry_mode / $registry_impl"

###############################################################################
# Verify Arabic resolution
###############################################################################

arabic_resolution="$(
    CHIMERA_COMMAND_ROOT="$CMDROOT" \
    CHIMERA_ROOT_PREFIX="$OUT" \
        "$BIN/chimera" help عرض
)"

grep -q '^عرض -> ls$' <<<"$arabic_resolution" || {
    die "Arabic alias resolution failed for عرض -> ls"
}

log "Arabic resolution: عرض -> ls"
'''

if old not in s:
    raise SystemExit(
        "Could not locate dispatcher validation block"
    )

s = s.replace(old, new)

p.write_text(s)
PY

###############################################################################
# 6. Add native mv implementation
###############################################################################

python3 - "$SOURCE" "$BUILDER" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
builder = Path(sys.argv[2])

s = source.read_text()

marker = """static int cmd_rm(int argc, char **argv)
"""

function = r'''static int cmd_mv(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: mv SOURCE DEST\n");
        return 2;
    }

    if (rename(argv[1], argv[2]) < 0) {
        perror("mv");
        return 1;
    }

    return 0;
}

'''

if "static int cmd_mv(" not in s:
    pos = s.find(marker)

    if pos < 0:
        raise SystemExit("Could not find cmd_rm() insertion point")

    s = s[:pos] + function + s[pos:]

old = r'''    if (!strcmp(cmd, "rm"))
        return cmd_rm(argc, argv);

    if (!strcmp(cmd, "cat"))
'''

new = r'''    if (!strcmp(cmd, "rm"))
        return cmd_rm(argc, argv);

    if (!strcmp(cmd, "mv"))
        return cmd_mv(argc, argv);

    if (!strcmp(cmd, "cat"))
'''

if old not in s:
    raise SystemExit("Could not add mv dispatcher entry")

s = s.replace(old, new)

source.write_text(s)

b = builder.read_text()

old_array = """    cp
    touch
"""

new_array = """    cp
    mv
    touch
"""

if old_array in b and "    mv\n" not in b[b.find("NATIVE_COMMANDS=("):b.find(")\n\nfor command")]:
    b = b.replace(old_array, new_array, 1)

old_registry = """mv\tنقل\tnative/system\tmv\tSS64/Linux
"""

new_registry = """mv\tنقل\tnative\tchimera-cmd\tSS64/Linux
"""

b = b.replace(old_registry, new_registry)

builder.write_text(b)
PY

###############################################################################
# 7. Add more native command aliases to the build manifest
###############################################################################

python3 - "$BUILDER" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

old = """    false
)
"""

new = """    false
    mv
)
"""

# Avoid duplicate insertion if already fixed.
start = s.find("NATIVE_COMMANDS=(")
end = s.find(")", start)

if start >= 0 and end >= 0:
    block = s[start:end]
    if "    mv" not in block:
        s = s[:end] + "    mv\n" + s[end:]

p.write_text(s)
PY

###############################################################################
# 8. Syntax validation
###############################################################################

echo "[CHECK] bash syntax..."
bash -n "$BUILDER"

echo "[CHECK] C source..."
cc \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -fsyntax-only \
    "$SOURCE"

echo "[OK] C source is warning-clean."

echo "[SUCCESS] Chimera command compatibility repair prepared."
echo
echo "Backups:"
echo "  $BACKUP"
