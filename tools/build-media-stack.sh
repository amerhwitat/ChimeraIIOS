#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-media-stack.sh

Usage:
  tools/build-media-stack.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_MEDIA_OUT:-$ROOT/build/media}"
TARGET="${CHIMERA_MEDIA_TARGET:-$(uname -m)}"
mkdir -p "$OUT/$TARGET"

: "${CHIMERA_MEDIA_ENABLE:=0}"
if [[ "$CHIMERA_MEDIA_ENABLE" != "1" ]]; then
  echo "Media build disabled. Set CHIMERA_MEDIA_ENABLE=1 to build upstream players."
  echo "Outputs: $OUT/$TARGET"
  exit 0
fi

: "${CHIMERA_MEDIA_WORK:=${TMPDIR:-/tmp}/chimera-media}"
mkdir -p "$CHIMERA_MEDIA_WORK"

fetch_and_verify() {
  local id="$1" url="$2" rev_var="$3"
  local rev="${!rev_var:-}"
  [[ -n "$rev" ]] || { echo "ERROR: $rev_var must be a pinned tag or commit" >&2; return 1; }
  local src="$CHIMERA_MEDIA_WORK/$id"
  if [[ ! -d "$src/.git" ]]; then
    git clone --filter=blob:none "$url" "$src"
  fi
  git -C "$src" fetch --tags --prune origin
  git -C "$src" checkout --detach "$rev"
  printf '%s %s\n' "$id" "$(git -C "$src" rev-parse HEAD)" >> "$OUT/$TARGET/revisions.txt"
  echo "$src"
}

if [[ -n "${CHIMERA_MEDIA_VLC_REV:-}" ]]; then
  src="$(fetch_and_verify vlc https://github.com/videolan/vlc CHIMERA_MEDIA_VLC_REV)"
  echo "VLC source prepared at $src"
fi
if [[ -n "${CHIMERA_MEDIA_MPV_REV:-}" ]]; then
  src="$(fetch_and_verify mpv https://github.com/mpv-player/mpv CHIMERA_MEDIA_MPV_REV)"
  echo "mpv source prepared at $src"
fi
if [[ -n "${CHIMERA_MEDIA_AUDACIOUS_REV:-}" ]]; then
  src="$(fetch_and_verify audacious https://github.com/audacious-media-player/audacious CHIMERA_MEDIA_AUDACIOUS_REV)"
  echo "Audacious source prepared at $src"
fi
if [[ -n "${CHIMERA_MEDIA_MPLAYER_REV:-}" ]]; then
  src="$(fetch_and_verify mplayer https://github.com/mplayerhq/mplayer CHIMERA_MEDIA_MPLAYER_REV)"
  echo "MPlayer source prepared at $src"
fi
if [[ -n "${CHIMERA_MEDIA_FFMPEG_REV:-}" ]]; then
  src="$(fetch_and_verify ffmpeg https://github.com/FFmpeg/FFmpeg CHIMERA_MEDIA_FFMPEG_REV)"
  echo "FFmpeg/FFplay source prepared at $src"
fi
if [[ -n "${CHIMERA_MEDIA_KODI_REV:-}" ]]; then
  src="$(fetch_and_verify kodi https://github.com/xbmc/xbmc CHIMERA_MEDIA_KODI_REV)"
  echo "Kodi source prepared at $src"
fi

cat > "$OUT/$TARGET/BUILD-POLICY.txt" <<'EOF'
Chimera II Aurora Media Stack
- Source revisions are pinned before production builds.
- Generated binaries must be accompanied by SHA-256 hashes and license/notice manifests.
- Proprietary codecs, firmware, player binaries and copyrighted recordings require separate licensing review.
- This script intentionally does not download unpinned or proprietary binary payloads.
EOF

echo "Media source preparation complete: $OUT/$TARGET"
