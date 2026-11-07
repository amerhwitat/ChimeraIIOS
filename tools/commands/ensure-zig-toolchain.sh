#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Ensure a pinned Zig C/C++ cross compiler is available for Linux ABI command builds.

Usage:
  tools/commands/ensure-zig-toolchain.sh

The toolchain is installed into build/toolchain-zig and does not modify system Python.
HELP
  exit 0
fi
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${CHIMERA_ZIG_VENV:-$ROOT/build/toolchain-zig}"
if command -v zig >/dev/null 2>&1; then
  zig version
  exit 0
fi
if [[ -x "$VENV/bin/python" ]] && "$VENV/bin/python" -m ziglang version >/dev/null 2>&1; then
  "$VENV/bin/python" -m ziglang version
  exit 0
fi
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required to provision Zig." >&2; exit 2; }
python3 -c 'import venv' >/dev/null 2>&1 || { echo "ERROR: install python3-venv before provisioning Zig." >&2; exit 2; }
mkdir -p "$(dirname "$VENV")"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check --no-input "ziglang==0.13.0"
"$VENV/bin/python" -m ziglang version
echo "Zig compiler ready at $VENV/bin/python -m ziglang"
