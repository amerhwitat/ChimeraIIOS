#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/src/chimera-command-compat/chimera-cmd.c"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CC="${CC:-cc}"
"$CC" -std=c11 -O2 -Wall -Wextra -Werror "$SRC" -o "$TMP/chimera-cmd"
for name in pwd echo ls cp mv touch mkdir rm cat clear whoami hostname date true false; do
  ln -s chimera-cmd "$TMP/$name"
done
test "$("$TMP/echo" genuine native command)" = "genuine native command"
test -n "$("$TMP/pwd")"
"$TMP/true"
if "$TMP/false"; then echo "false returned success" >&2; exit 1; fi
test -n "$("$TMP/date")"
test -n "$("$TMP/hostname")"
test -n "$(env -u USER "$TMP/whoami")"
printf 'copy-payload' > "$TMP/source"
"$TMP/cp" "$TMP/source" "$TMP/copied"
test "$(cat "$TMP/copied")" = "copy-payload"
"$TMP/mv" "$TMP/copied" "$TMP/moved"
test ! -e "$TMP/copied"
test "$(cat "$TMP/moved")" = "copy-payload"
"$TMP/mkdir" "$TMP/directory"
test -d "$TMP/directory"
"$TMP/rm" "$TMP/moved"
test ! -e "$TMP/moved"
python3 - "$TMP/touched" <<'PY'
import os,sys,time
p=sys.argv[1]
with open(p,"w") as f: f.write("touch")
old=time.time()-120
os.utime(p,(old,old))
PY
"$TMP/touch" "$TMP/touched"
python3 - "$TMP/touched" <<'PY'
import os,sys,time
assert os.stat(sys.argv[1]).st_mtime > time.time()-10, "touch did not update mtime"
PY
"$TMP/ls" "$TMP" | grep -q source
test "$("$TMP/cat" "$TMP/source")" = "copy-payload"
banner="$("$TMP/chimera-cmd")"
grep -q "Readiness: not asserted" <<<"$banner"
if grep -qi "Status: operational" <<<"$banner"; then echo "false readiness banner remains" >&2; exit 1; fi
echo "PASS: all 15 registered native multicall command entry points passed host semantic smoke tests."
