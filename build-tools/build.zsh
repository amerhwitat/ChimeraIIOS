#!/usr/bin/env zsh
set -e
ROOT=${0:A:h:h}
command -v python3 >/dev/null || { print '[DEPENDENCY] Python 3 not found.'; exit 2; }
exec python3 "$ROOT/build-tools/build.py" "$@"
