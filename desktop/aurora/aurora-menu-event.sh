#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVENT="${1:-}"
[[ -n "$EVENT" ]] || exit 0
exec bash "$ROOT/aurora-event-sound.sh" "$EVENT"
