#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_FOREIGN_ROOT:-$ROOT/build/foreign}"
SRC="$OUT/source"
BIN="$OUT/binaries"
META="$OUT/metadata"
mkdir -p "$SRC" "$BIN" "$META"
MANIFEST="$ROOT/config/foreign-runtime-sources.json"
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 2; }
python3 - "$MANIFEST" "$OUT" <<'PY'
import json,sys,pathlib
m=json.load(open(sys.argv[1])); out=pathlib.Path(sys.argv[2])
for group in ("windows","macos","desktops","mobile"):
    for p in m.get(group,{}).get("source_projects",[]):
        (out/"metadata"/f"{group}-{p['name'].lower().replace(' ','-')}.json").write_text(json.dumps(p,indent=2)+"\n")
PY

# Linux binaries are acquired from the host's signed package repositories.
# Never scrape arbitrary binaries: repository metadata and package signatures
# remain the trust boundary.
if command -v apt-get >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
  mkdir -p "$BIN/deb"
  mapfile -t packages < <(python3 - "$MANIFEST" <<'PY'
import json,sys
print("\n".join(json.load(open(sys.argv[1]))["linux"]["packages"]))
PY
)
  for p in "${packages[@]}"; do
    (cd "$BIN/deb" && apt-get download "$p" >/dev/null 2>&1) || echo "SKIP package: $p"
  done
fi

if [[ "${CHIMERA_FETCH_SOURCES:-1}" == "1" ]]; then
  while IFS=$'\t' read -r name url; do
    dir="$SRC/${name// /_}"
    if [[ -d "$dir/.git" ]]; then git -C "$dir" fetch --depth=1 origin; continue; fi
    git clone --depth=1 "$url" "$dir"
  done < <(python3 - "$MANIFEST" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
for group in ("windows","macos","desktops","mobile"):
  for p in m.get(group,{}).get("source_projects",[]):
    print(p["name"]+"\t"+p["repository"])
PY
)
fi

find "$OUT" -type f -printf '%P\n' | sort > "$META/file-index.txt"
sha256sum $(find "$OUT" -type f ! -path '*/file-index.txt' -print) > "$META/SHA256SUMS" 2>/dev/null || true
printf 'Foreign runtime staging complete: %s\n' "$OUT"
