#!/usr/bin/env bash
set -Eeuo pipefail
shell="${1:-bash}"
case "$shell" in
  bash|zsh|fish|dash|mksh|yash|elvish) exec "$shell" ;;
  nu|nushell) exec nu ;;
  *) echo "Unknown Chimera shell: $shell" >&2; exit 2 ;;
esac
