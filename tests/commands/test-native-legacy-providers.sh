#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cc -std=c11 -O2 -Wall -Wextra -Werror "$ROOT/tools/commands/native/write.c" -o "$tmp/write"
cc -std=c11 -O2 -Wall -Wextra -Werror "$ROOT/tools/commands/native/fdformat.c" -o "$tmp/fdformat"
"$tmp/fdformat" --help >/dev/null
set +e
"$tmp/fdformat" /dev/null >"$tmp/fdformat.out" 2>&1
fdformat_rc=$?
"$tmp/write" chimera-user-that-does-not-exist </dev/null >"$tmp/write.out" 2>&1
write_rc=$?
set -e
[[ "$fdformat_rc" -ne 0 ]]
grep -q "cannot read floppy geometry" "$tmp/fdformat.out"
[[ "$write_rc" -eq 1 ]]
grep -q "is not logged in" "$tmp/write.out"
echo "Native write/fdformat provider compile and safe-failure tests: PASS"
