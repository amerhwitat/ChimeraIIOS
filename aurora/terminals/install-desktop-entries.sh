#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR is required}"
MANIFEST="$ROOTFS/usr/share/chimera/aurora/terminal-shell-staging.json"
APPS="$ROOTFS/usr/share/applications"
mkdir -p "$APPS"
[[ -s "$MANIFEST" ]] || { echo "[AURORA-TERMINAL] staging manifest missing; no launchers emitted" >&2; exit 1; }
python3 - "$ROOTFS" "$MANIFEST" "$APPS" <<'PY'
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); manifest=json.loads(pathlib.Path(sys.argv[2]).read_text()); apps=pathlib.Path(sys.argv[3])
names={"xterm":"XTerm","gnome-terminal":"GNOME Terminal","konsole":"Konsole","xfce4-terminal":"XFCE Terminal",
       "foot":"Foot","kitty":"Kitty","alacritty":"Alacritty","wezterm":"WezTerm","ghostty":"Ghostty","contour":"Contour"}
for row in manifest.get("entries",[]):
    if row.get("kind")!="terminal" or row.get("status") not in ("binary-present","verified-elf-provider") or row.get("runtime_status")!="version-smoke-pass":
        continue
    path=row.get("path","")
    if not path or not (root/path.lstrip("/")).is_file() or not (root/path.lstrip("/")).stat().st_mode&0o111: continue
    ident=row["id"]; binary=row["binary"]
    (apps/f"chimera-terminal-{ident}.desktop").write_text(
      "[Desktop Entry]\nType=Application\nName="+names.get(ident,ident)+"\nExec="+path+
      "\nTerminal=false\nCategories=System;TerminalEmulator;\nX-Chimera-Aurora=true\n")
print("[AURORA-TERMINAL] generated desktop entries only for present executable terminal providers")
PY
