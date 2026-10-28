#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then echo "Usage: $0 <executable> [args...]" >&2; exit 64; fi
app="$1"; shift
[[ -e "$app" ]] || { echo "ERROR: application not found: $app" >&2; exit 66; }
if command -v file >/dev/null 2>&1; then
  kind="$(file -b "$app" 2>/dev/null || true)"
  case "$kind" in
    *Mach-O*)
      if [[ -n "${CHIMERA_DARWIN_RUNTIME:-}" && -x "${CHIMERA_DARWIN_RUNTIME}" ]]; then
        exec "$CHIMERA_DARWIN_RUNTIME" "$app" "$@"
      fi
      echo "UNSUPPORTED: this is a Mach-O/macOS binary. The OS currently has no verified Darwin ABI/Frameworks runtime; use a portable GNUstep build or run it on macOS." >&2
      exit 78
      ;;
  esac
fi
# Compatibility environment for portable apps using the supported POSIX/GNUstep surface.
export CHIMERA_MACOS_COMPAT=1
export OCTAVIAN_MACOS_COMPAT=1
export MACOS_COMPAT_PROFILE="${MACOS_COMPAT_PROFILE:-portable-posix}"
exec "$app" "$@"
