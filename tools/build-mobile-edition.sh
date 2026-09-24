#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_MOBILE_BUILD_DIR:-$ROOT/build/mobile}"
mkdir -p "$OUT/bin" "$OUT/source" "$OUT/manifests" "$OUT/apps" "$OUT/flash"
cp "$ROOT/config/mobile-os-sources.json" "$OUT/manifests/mobile-os-sources.json"
cp "$ROOT/mobile/flash/mobile-flash-tool.sh" "$OUT/flash/mobile-flash-tool.sh"
cp "$ROOT/mobile/flash/device-manifest.schema.json" "$OUT/manifests/device-manifest.schema.json"
chmod +x "$OUT/flash/mobile-flash-tool.sh"
cp "$ROOT/config/foreign-runtime-sources.json" "$OUT/manifests/"
stage_source_tree() {
  local name="$1"
  local src="$ROOT/build/foreign/source/$name"
  local dst="$OUT/source/$name"

  [[ -d "$src" ]] || return 0
  rm -rf "$dst"
  mkdir -p "$dst"

  # A foreign source checkout can contain a root-owned or otherwise
  # unwritable .git object database from a previous container build.
  # Mobile ISO staging needs the working tree, not Git's internal database.
  # Export HEAD when possible so .git is never copied into the ISO staging tree.
  if [[ -d "$src/.git" ]] && command -v git >/dev/null 2>&1 && git -C "$src" rev-parse --verify HEAD >/dev/null 2>&1; then
    if git -C "$src" archive --format=tar HEAD | tar -x -C "$dst"; then
      return 0
    fi
    rm -rf "$dst"
    mkdir -p "$dst"
  fi

  # Fallback for non-Git source trees. GNU cp cannot exclude .git, so use
  # tar's exclude support when available and preserve normal user ownership.
  if command -v tar >/dev/null 2>&1; then
    tar -C "$src" --exclude=.git -cf - . | tar -C "$dst" -xf -
  else
    find "$src" -mindepth 1 -maxdepth 1 ! -name .git -exec cp -a -- {} "$dst/" \;
  fi
}

stage_source_tree AOSP
stage_source_tree LineageOS
stage_source_tree Plasma_Mobile
cat > "$OUT/manifests/mobile-edition.json" <<'EOF'
{"schema":"CHM-MOBILE-EDITION-1","architectures":["arm64-v8a","armeabi-v7a","x86_64"],"editions":["Chimera Mobile","Aurora Mobile","Plasma Mobile compatibility"],"source_stage":"source","binary_stage":"bin","apps_stage":"apps","flash_stage":"flash","open_source_os_catalog":"mobile-os-sources.json","policy":"build-from-source-or-licensed-redistributable-only"}
EOF
printf 'Mobile edition scaffold: %s\n' "$OUT"
