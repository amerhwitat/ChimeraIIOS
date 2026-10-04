#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-font-pack.sh

Usage:
  tools/build-font-pack.sh [options] [arguments]

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
OUT="${CHIMERA_FONT_OUT:-$ROOT/build/fonts}"
TARGET="${CHIMERA_FONT_TARGET:-$(uname -m)}"
WORK="${CHIMERA_FONT_WORK:-${TMPDIR:-/tmp}/chimera-fonts}"
mkdir -p "$OUT/$TARGET" "$WORK"

cat > "$OUT/$TARGET/FONT-POLICY.txt" <<'EOF'
Chimera II OS free-font policy:
- Fetch only explicitly approved upstream font projects.
- Pin revisions before production packaging.
- Preserve upstream license and attribution files.
- Generate SHA-256 hashes for every bundled font file.
- Do not bundle proprietary fonts.
EOF

fetch() {
  local id="$1" url="$2" rev_var="$3"
  local rev="${!rev_var:-}"
  [[ -n "$rev" ]] || { echo "ERROR: $rev_var must contain a pinned tag/commit" >&2; return 1; }
  local src="$WORK/$id"
  [[ -d "$src/.git" ]] || git clone --filter=blob:none "$url" "$src"
  git -C "$src" fetch --tags --prune origin
  git -C "$src" checkout --detach "$rev"
  echo "$id $(git -C "$src" rev-parse HEAD)" >> "$OUT/$TARGET/revisions.txt"
  printf '%s\n' "$src"
}

copy_fonts() {
  local id="$1" src="$2" dst="$OUT/$TARGET/$id"
  mkdir -p "$dst"
  find "$src" -type f \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.woff' -o -iname '*.woff2' \) -print0 |
    while IFS= read -r -d '' f; do
      install -Dm644 "$f" "$dst/$(basename "$f")"
      sha256sum "$f" >> "$OUT/$TARGET/SHA256SUMS"
    done
}

for spec in \
  "dejavu|https://github.com/dejavu-fonts/dejavu-fonts|CHIMERA_FONT_DEJAVU_REV" \
  "noto-latin|https://github.com/notofonts/latin|CHIMERA_FONT_NOTO_LATIN_REV" \
  "noto-arabic|https://github.com/notofonts/arabic|CHIMERA_FONT_NOTO_ARABIC_REV" \
  "noto-hebrew|https://github.com/notofonts/hebrew|CHIMERA_FONT_NOTO_HEBREW_REV" \
  "noto-indic|https://github.com/notofonts/indic|CHIMERA_FONT_NOTO_INDIC_REV" \
  "noto-cjk|https://github.com/notofonts/noto-cjk|CHIMERA_FONT_NOTO_CJK_REV" \
  "noto-emoji|https://github.com/googlefonts/noto-emoji|CHIMERA_FONT_NOTO_EMOJI_REV" \
  "liberation|https://github.com/liberationfonts/liberation-fonts|CHIMERA_FONT_LIBERATION_REV" \
  "freefont|https://git.savannah.gnu.org/git/freefont.git|CHIMERA_FONT_FREEFONT_REV" \
  "unifont|https://github.com/gnu-unifont/unifont|CHIMERA_FONT_UNIFONT_REV" \
  "texgyre|https://github.com/Font-Repository/tex-gyre|CHIMERA_FONT_TEXGYRE_REV"; do
  IFS='|' read -r id url var <<< "$spec"
  if [[ -n "${!var:-}" ]]; then
    src="$(fetch "$id" "$url" "$var")"
    copy_fonts "$id" "$src"
  fi
done

echo "Font package preparation complete: $OUT/$TARGET"
