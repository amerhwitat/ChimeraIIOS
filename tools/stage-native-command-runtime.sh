#!/usr/bin/env bash
# Stage the native Chimera multicall applets without replacing host/coreutils commands.
# Usage: tools/stage-native-command-runtime.sh SOURCE_ROOT DEST_ROOT
set -Eeuo pipefail

SOURCE_ROOT="${1:-}"
DEST_ROOT="${2:-}"
[[ -n "$SOURCE_ROOT" && -n "$DEST_ROOT" ]] || {
  echo "usage: $0 SOURCE_ROOT DEST_ROOT" >&2
  exit 2
}
SOURCE_ROOT="$(cd -- "$SOURCE_ROOT" && pwd)"
mkdir -p "$DEST_ROOT/bin" "$DEST_ROOT/usr/bin" "$DEST_ROOT/usr/lib/chimera/native-bin" "$DEST_ROOT/usr/share/chimera"
NATIVE_BIN="$DEST_ROOT/usr/lib/chimera/native-bin"
CC="${CC:-gcc}"
command -v "$CC" >/dev/null 2>&1 || { echo "ERROR: C compiler not found: $CC" >&2; exit 2; }
COMMAND_SRC="$SOURCE_ROOT/src/chimera-command-compat/chimera-cmd.c"
test -s "$COMMAND_SRC" || { echo "ERROR: native command source missing: $COMMAND_SRC" >&2; exit 2; }

if [[ "${CHIMERA_COMMAND_LINK_MODE:-dynamic}" == "static" ]]; then
  "$CC" -std=c11 -O2 -Wall -Wextra -Werror -static "$COMMAND_SRC" -o "$NATIVE_BIN/chimera-cmd"
else
  "$CC" -std=c11 -O2 -Wall -Wextra -Werror "$COMMAND_SRC" -o "$NATIVE_BIN/chimera-cmd"
fi
chmod 0755 "$NATIVE_BIN/chimera-cmd"

NATIVE_COMMANDS=(pwd echo ls cp mv touch mkdir rm cat clear whoami hostname date true false)
for command in "${NATIVE_COMMANDS[@]}"; do
  ln -sfn chimera-cmd "$NATIVE_BIN/$command"
done

cat > "$DEST_ROOT/usr/bin/chimera-native" <<'WRAPPER'
#!/bin/sh
set -eu
command="${1:-}"
if [ -z "$command" ]; then
  echo "usage: chimera-native COMMAND [ARGS...]" >&2
  exit 2
fi
shift
prefix="${CHIMERA_ROOT_PREFIX:-}"
if [ -n "$prefix" ]; then
  native_bin="$prefix/usr/lib/chimera/native-bin"
else
  native_bin="/usr/lib/chimera/native-bin"
fi
exec "$native_bin/$command" "$@"
WRAPPER
chmod 0755 "$DEST_ROOT/usr/bin/chimera-native"
if [[ "$(readlink -f "$DEST_ROOT/bin")" != "$(readlink -f "$DEST_ROOT/usr/bin")" ]]; then
  ln -sfn ../usr/bin/chimera-native "$DEST_ROOT/bin/chimera-native"
fi

if [[ "${CHIMERA_STAGE_CATALOGS:-1}" == "1" ]]; then
  mkdir -p "$DEST_ROOT/usr/share/chimera/commands/catalogs" "$DEST_ROOT/usr/share/chimera/isa" \
           "$DEST_ROOT/usr/share/chimera/source/commands" "$DEST_ROOT/usr/share/chimera/source/isa" \
           "$DEST_ROOT/usr/share/chimera/source/command-tools" "$DEST_ROOT/usr/share/chimera/source/isa-tools" \
           "$DEST_ROOT/usr/share/chimera/source/include/chimera"
  cp -a "$SOURCE_ROOT/system/commands/." "$DEST_ROOT/usr/share/chimera/commands/catalogs/"
  cp -a "$SOURCE_ROOT/isa/." "$DEST_ROOT/usr/share/chimera/isa/"
  [[ ! -f "$SOURCE_ROOT/ISA.csv" ]] || cp -f "$SOURCE_ROOT/ISA.csv" "$DEST_ROOT/usr/share/chimera/isa/ISA.csv"
  cp -a "$SOURCE_ROOT/src/chimera-command-compat/." "$DEST_ROOT/usr/share/chimera/source/commands/"
  cp -a "$SOURCE_ROOT/src/isa/." "$DEST_ROOT/usr/share/chimera/source/isa/"
  cp -a "$SOURCE_ROOT/tools/commands/." "$DEST_ROOT/usr/share/chimera/source/command-tools/"
  cp -a "$SOURCE_ROOT/tools/isa/." "$DEST_ROOT/usr/share/chimera/source/isa-tools/"
  [[ ! -f "$SOURCE_ROOT/include/chimera/isa8192.hpp" ]] || cp -f "$SOURCE_ROOT/include/chimera/isa8192.hpp" "$DEST_ROOT/usr/share/chimera/source/include/chimera/"
fi

if [[ "${CHIMERA_INSTALL_DISPATCHER:-1}" == "1" ]]; then
  command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 is required for the compatibility dispatcher" >&2; exit 2; }
  mkdir -p "$DEST_ROOT/usr/share/chimera/commands"
  install -m 0755 "$SOURCE_ROOT/tools/commands/chimera-run" "$DEST_ROOT/usr/share/chimera/commands/chimera-run"
  install -m 0644 "$SOURCE_ROOT/tools/commands/os-command-runtime.json" "$DEST_ROOT/usr/share/chimera/commands/os-command-runtime.json"
  ln -sfn ../share/chimera/commands/chimera-run "$DEST_ROOT/usr/bin/chimera-run"
  cat > "$DEST_ROOT/usr/bin/chimera" <<'DISPATCH'
#!/bin/sh
set -eu
export PATH="/usr/lib/chimera/native-bin:$PATH"
exec python3 /usr/share/chimera/commands/chimera-run "$@"
DISPATCH
  chmod 0755 "$DEST_ROOT/usr/bin/chimera"
  python3 "$DEST_ROOT/usr/share/chimera/commands/chimera-run" --list >/dev/null
fi

"$NATIVE_BIN/echo" "Chimera native command runtime staged" >/dev/null
CHIMERA_ROOT_PREFIX="$DEST_ROOT" "$DEST_ROOT/usr/bin/chimera-native" echo "Chimera native wrapper staged" >/dev/null
printf 'CHIMERA_NATIVE_COMMANDS=%s\nCHIMERA_COMMAND_LINK_MODE=%s\nCHIMERA_DISPATCHER=%s\n' \
  "${#NATIVE_COMMANDS[@]}" "${CHIMERA_COMMAND_LINK_MODE:-dynamic}" "${CHIMERA_INSTALL_DISPATCHER:-1}" \
  > "$DEST_ROOT/usr/share/chimera/runtime-stage.env"
