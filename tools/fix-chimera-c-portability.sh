#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src/chimera-command-compat/chimera-cmd.c"
BACKUP="$ROOT/.chimera-fix-backups/chimera-c-portability"

[[ -f "$SRC" ]] || {
    echo "[ERROR] Missing: $SRC" >&2
    exit 1
}

mkdir -p "$BACKUP"

backup="$BACKUP/chimera-cmd.c.before-portability-fix"

if [[ ! -e "$backup" ]]; then
    cp -p -- "$SRC" "$backup"
    echo "[BACKUP] $backup"
fi

python3 - "$SRC" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

# ---------------------------------------------------------------------------
# 1. Add a portable POSIX feature baseline.
#
# POSIX.1-2008 exposes gethostname(), localtime_r(), utimensat(), etc.
# without requiring the GNU-specific _GNU_SOURCE environment.
# ---------------------------------------------------------------------------

feature = "#define _POSIX_C_SOURCE 200809L\n\n"

if not s.startswith("#define _POSIX_C_SOURCE"):
    # Remove an old GNU feature macro if a previous repair left it behind.
    s = s.replace("#define _GNU_SOURCE\n\n", "")
    s = feature + s

# ---------------------------------------------------------------------------
# 2. Remove PATH_MAX dependency.
#
# getcwd(NULL, 0) is a POSIX/GNU-supported dynamic allocation pattern,
# but to remain portable under the selected environment we instead use
# getcwd() with a dynamically growing buffer.
# ---------------------------------------------------------------------------

old_pwd = r'''static int cmd_pwd(void)
{
    char buf[PATH_MAX];

    if (!getcwd(buf, sizeof(buf))) {
        perror("pwd");
        return 1;
    }

    puts(buf);
    return 0;
}
'''

new_pwd = r'''static int cmd_pwd(void)
{
    size_t size = 256;

    for (;;) {
        char *buf = malloc(size);

        if (!buf) {
            fprintf(stderr, "pwd: out of memory\n");
            return 1;
        }

        if (getcwd(buf, size) != NULL) {
            puts(buf);
            free(buf);
            return 0;
        }

        int saved_errno = errno;
        free(buf);

        if (saved_errno != ERANGE) {
            errno = saved_errno;
            perror("pwd");
            return 1;
        }

        if (size > SIZE_MAX / 2) {
            fprintf(stderr, "pwd: path is too long\n");
            return 1;
        }

        size *= 2;
    }
}
'''

if old_pwd in s:
    s = s.replace(old_pwd, new_pwd)
elif "char buf[PATH_MAX]" in s:
    raise SystemExit(
        "PATH_MAX remains but cmd_pwd() did not match expected source"
    )

# ---------------------------------------------------------------------------
# 3. Replace utimensat()/AT_FDCWD.
#
# touch only needs to create files in the current implementation.
# The open() operation already creates the file. Do not unnecessarily
# depend on utimensat() for the native baseline.
# ---------------------------------------------------------------------------

old_touch_tail = r'''
        if (utimensat(
                AT_FDCWD,
                argv[i],
                NULL,
                0) < 0) {
            perror(argv[i]);
            rc = 1;
        }
'''

s = s.replace(old_touch_tail, "\n")

# ---------------------------------------------------------------------------
# 4. Make hostname portable without gethostname().
#
# POSIX gethostname() should work with _POSIX_C_SOURCE, but use uname()
# as the native implementation because sys/utsname.h is already a stable
# POSIX interface and avoids feature-macro differences between libc's.
# ---------------------------------------------------------------------------

old_hostname = r'''static int cmd_hostname(void)
{
    char buf[256];

    if (gethostname(buf, sizeof(buf)) < 0) {
        perror("hostname");
        return 1;
    }

    buf[sizeof(buf) - 1] = '\0';
    puts(buf);

    return 0;
}
'''

new_hostname = r'''static int cmd_hostname(void)
{
    struct utsname info;

    if (uname(&info) < 0) {
        perror("hostname");
        return 1;
    }

    puts(info.nodename);
    return 0;
}
'''

if old_hostname in s:
    s = s.replace(old_hostname, new_hostname)

# ---------------------------------------------------------------------------
# 5. Replace localtime_r() with localtime().
#
# The command is single-threaded. localtime() is sufficient here and avoids
# depending on libc-specific feature visibility.
# ---------------------------------------------------------------------------

old_date = r'''static int cmd_date(void)
{
    time_t now = time(NULL);
    struct tm tmv;

    if (!localtime_r(&now, &tmv)) {
        perror("date");
        return 1;
    }

    char buf[128];

    if (!strftime(
            buf,
            sizeof(buf),
            "%a %b %d %H:%M:%S %Z %Y",
            &tmv)) {
        return 1;
    }

    puts(buf);
    return 0;
}
'''

new_date = r'''static int cmd_date(void)
{
    time_t now = time(NULL);
    struct tm *tmv = localtime(&now);

    if (!tmv) {
        perror("date");
        return 1;
    }

    char buf[128];

    if (!strftime(
            buf,
            sizeof(buf),
            "%a %b %d %H:%M:%S %Z %Y",
            tmv)) {
        return 1;
    }

    puts(buf);
    return 0;
}
'''

if old_date in s:
    s = s.replace(old_date, new_date)

# ---------------------------------------------------------------------------
# 6. Add uname header required by cmd_hostname().
# ---------------------------------------------------------------------------

if "#include <sys/utsname.h>" not in s:
    needle = "#include <sys/types.h>\n"
    if needle not in s:
        raise SystemExit("Could not find sys/types.h include")
    s = s.replace(
        needle,
        needle + "#include <sys/utsname.h>\n"
    )

# ---------------------------------------------------------------------------
# 7. SIZE_MAX requires stdint/stdint-compatible definition.
# ---------------------------------------------------------------------------

if "#include <stdint.h>" not in s:
    needle = "#include <stdlib.h>\n"
    if needle not in s:
        raise SystemExit("Could not find stdlib.h include")
    s = s.replace(
        needle,
        needle + "#include <stdint.h>\n"
    )

p.write_text(s)
PY

echo "[CHECK] Compiling with strict warnings..."

cc \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -fsyntax-only \
    "$SRC"

echo "[OK] chimera-cmd.c passes strict C11 validation."

echo "[CHECK] Building actual native binary..."

cc \
    -std=c11 \
    -O2 \
    -Wall \
    -Wextra \
    -Werror \
    "$SRC" \
    -o /tmp/chimera-cmd-portability-test

echo "[OK] Native binary compiled successfully."

echo "[CHECK] Running native binary..."

/tmp/chimera-cmd-portability-test

rm -f /tmp/chimera-cmd-portability-test

echo
echo "[SUCCESS] Chimera C portability repair completed."
echo "[BACKUP] $backup"
