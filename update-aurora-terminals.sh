#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
BUILD_DIR="${CHIMERA_BUILD_DIR:-/mnt/d/chimera-build}"
SOURCE_ROOTFS="${CHIMERA_ROOTFS:-$ROOT/rootfs}"
AURORA_DIR="$ROOT/desktop/aurora"
TOOLS_DIR="$ROOT/tools/aurora"
GEN="$TOOLS_DIR/generate-applications-menu.sh"
ORCH="$ROOT/koronos-build-orchestrator.sh"

log(){ printf '[AURORA-TERMINALS] %s\n' "$*"; }
die(){ echo "[AURORA-TERMINALS][ERROR] $*" >&2; exit 1; }

[[ -d "$ROOT" ]] || die "Chimera source tree not found: $ROOT"
mkdir -p "$TOOLS_DIR"

cat > "$GEN" <<'GENEOF'
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
ROOTFS="${CHIMERA_ROOTFS:-$ROOT/rootfs}"
OUT="${CHIMERA_AURORA_APPS_OUT:-$ROOTFS/usr/share/applications}"
TERM_OUT="$OUT/chimera-terminals"
META_OUT="${CHIMERA_AURORA_META_OUT:-$ROOT/build/aurora}"
MANIFEST="$META_OUT/terminal-applications.txt"

log(){ printf '[AURORA-MENU] %s\n' "$*"; }
mkdir -p "$OUT" "$TERM_OUT" "$META_OUT"
rm -f "$TERM_OUT"/*.desktop "$MANIFEST"
: > "$MANIFEST"

# Known graphical terminal desktop IDs. We do not require these packages to be
# installed: entries are generated only when a real executable or .desktop file
# exists in the target rootfs.
KNOWN=(
  konsole gnome-terminal xfce4-terminal mate-terminal qterminal tilix terminator
  alacritty kitty wezterm foot xterm urxvt rxvt st cool-retro-term tilda guake
  yakuake ptyxis blackbox contour hyper terminology sakura eterm mlterm
)

# Resolve an executable inside the target rootfs without executing it.
find_exec(){
  local n="$1" p
  for p in "$ROOTFS/usr/bin/$n" "$ROOTFS/bin/$n" "$ROOTFS/usr/local/bin/$n"; do
    [[ -x "$p" ]] && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}

# Copy/normalize existing desktop files. Prefer the target rootfs, but also
# inspect source-side application directories when the build uses overlays.
copy_desktop(){
  local id="$1" f
  for f in \
    "$ROOTFS/usr/share/applications/$id.desktop" \
    "$ROOTFS/usr/local/share/applications/$id.desktop" \
    "$ROOT/usr/share/applications/$id.desktop"; do
    if [[ -f "$f" ]]; then
      cp -f -- "$f" "$TERM_OUT/$id.desktop"
      return 0
    fi
  done
  return 1
}

# If an installed desktop file advertises TerminalEmulator, include it even
# when it is not in the curated list. This is the future-proof discovery path.
shopt -s nullglob
for d in "$ROOTFS/usr/share/applications" "$ROOTFS/usr/local/share/applications"; do
  [[ -d "$d" ]] || continue
  for f in "$d"/*.desktop; do
    grep -Eiq '^Categories=.*(^|;)TerminalEmulator(;|$)|^Categories=.*TerminalEmulator' "$f" || continue
    id="$(basename "$f")"
    cp -f -- "$f" "$TERM_OUT/$id"
  done
done

for id in "${KNOWN[@]}"; do
  if [[ -f "$TERM_OUT/$id.desktop" ]]; then
    printf '%s\n' "$id.desktop" >> "$MANIFEST"
    continue
  fi
  copy_desktop "$id" && { printf '%s\n' "$id.desktop" >> "$MANIFEST"; continue; }
  if exe="$(find_exec "$id" 2>/dev/null)"; then
    cat > "$TERM_OUT/$id.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=$(printf '%s' "$id" | sed 's/[-_]/ /g')
Comment=Terminal emulator
Exec=$exe
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;Utility;
Keywords=terminal;shell;console;command line;
StartupNotify=true
EOF2
    printf '%s\n' "$id.desktop" >> "$MANIFEST"
  fi
done

# De-duplicate by desktop filename and then sort deterministically.
sort -u "$MANIFEST" -o "$MANIFEST"

# Install discovered terminal entries into the normal application directory.
# This lets GTK/KDE/XDG menus discover them without requiring Aurora-specific
# hard-coded names.
while IFS= read -r f; do
  [[ -f "$TERM_OUT/$f" ]] || continue
  cp -f -- "$TERM_OUT/$f" "$OUT/$f"
done < "$MANIFEST"

# Rebuild the XDG desktop database if available. Never fail the build merely
# because the helper is absent in a minimal build environment.
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$OUT" >/dev/null 2>&1 || true
elif [[ -x "$ROOTFS/usr/bin/update-desktop-database" ]]; then
  chroot "$ROOTFS" /usr/bin/update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

# Emit a machine-readable Aurora inventory for menu implementations that use
# JSON rather than XDG desktop discovery.
python3 - "$MANIFEST" "$META_OUT/terminals.json" <<'PY'
import json, pathlib, sys
manifest=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
items=[]
for line in manifest.read_text(encoding='utf-8').splitlines():
    if line.strip():
        items.append({"desktop":line.strip(),"category":"TerminalEmulator"})
out.write_text(json.dumps({"schema":"CHIMERA-AURORA-TERMINALS-1","applications":items},indent=2)+"\n",encoding='utf-8')
PY

log "Discovered $(wc -l < "$MANIFEST") terminal applications."
log "Inventory: $MANIFEST"
GENEOF
chmod +x "$GEN"

# Hook the menu-generation stage into the existing dependency-aware build
# orchestrator immediately before ISO consumers. It is idempotent.
if [[ -f "$ORCH" ]]; then
  cp -a -- "$ORCH" "$ORCH.bak-aurora-terminals-$(date +%Y%m%d-%H%M%S)"
  python3 - "$ORCH" <<'PY'
from pathlib import Path
p=Path(__import__('sys').argv[1])
s=p.read_text()
marker='# Stage 4: independent post-Koronos tasks may run together, but only\n'
needle=marker
hook='''# ------------------------------------------------------------\n# Stage 4a: Aurora Applications/menu generation. This must happen\n# after the rootfs/application payload is present and before ISO\n# mastering so the generated XDG/Aurora terminal entries are captured.\n# ------------------------------------------------------------\nif [[ -x "$ROOT/tools/aurora/generate-applications-menu.sh" ]]; then\n    run_step "aurora-applications-menu" bash "$ROOT/tools/aurora/generate-applications-menu.sh" \\\n        || die "Aurora Applications/menu generation failed."\nfi\n\n'''
if 'run_step "aurora-applications-menu"' not in s:
    if marker not in s:
        raise SystemExit('orchestrator marker not found')
    s=s.replace(needle,hook+needle,1)
    p.write_text(s)
PY
  bash -n "$ORCH"
else
  log "Orchestrator not found; generator was installed and can be invoked by the build manually."
fi

# Also provide a direct stage runner for builds that do not use the orchestrator.
RUNNER="$TOOLS_DIR/update-aurora-applications.sh"
cat > "$RUNNER" <<'EOF2'
#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
exec "$ROOT/tools/aurora/generate-applications-menu.sh" "$@"
EOF2
chmod +x "$RUNNER"

log "Aurora application/menu generation updated."
log "Generator: $GEN"
log "Runner: $RUNNER"
[[ -f "$ORCH" ]] && log "Build orchestrator hooked and syntax-validated: $ORCH"
