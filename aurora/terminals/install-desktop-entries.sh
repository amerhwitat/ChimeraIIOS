#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: $0  (requires CHIMERA_ROOTFS_DIR containing the staged target root filesystem)"
  exit 0
fi
ROOTFS="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR is required}"
APPS="$ROOTFS/usr/share/applications"
AUDIT="$ROOTFS/usr/share/chimera/aurora/terminal-shell-provider-audit.json"
mkdir -p "$APPS"
python3 - "$ROOTFS" "$APPS" "$AUDIT" <<'PY'
import json,sys
from pathlib import Path
root,apps,audit=map(Path,sys.argv[1:])
if audit.exists():
    rows=json.loads(audit.read_text()).get("entries",[])
else:
    rows=[]
    for kind,reg in (("terminal",root/"usr/share/chimera/aurora/terminals/registry.json"),("shell",root/"usr/share/chimera/aurora/shells/registry.json")):
        if reg.exists():
            for x in json.loads(reg.read_text()).get("entries",[]):
                b=x["binary"]; p=next((q for q in (root/"usr/bin"/b,root/"bin"/b,root/"usr/local/bin"/b) if q.exists() and q.is_file()),None)
                rows.append({"kind":kind,"id":x["id"],"name":x["name"],"binary":b,"status":"present" if p else "provider-missing"})
for x in rows:
    if x.get("status")!="verified-elf-provider" and x.get("status")!="present": continue
    kind=x["kind"]; ident=x["id"]; name=x["name"]; binary=x["binary"]
    if kind=="terminal":
        desktop=f"""[Desktop Entry]
Type=Application
Name={name}
Comment=Aurora terminal emulator
Exec={binary}
Terminal=false
Icon=chimera-terminal
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Terminal-ID={ident}
"""
    else:
        shellarg="nu" if ident=="nushell" else ident
        desktop=f"""[Desktop Entry]
Type=Application
Name={name} Shell
Comment=Open an Aurora session in {name}
Exec=/usr/lib/chimera/aurora/launch-shell.sh {shellarg}
Terminal=true
Icon=chimera-terminal
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Shell-ID={ident}
"""
    (apps/f"chimera-{kind}-{ident}.desktop").write_text(desktop)
center=next((p for p in (root/"usr/bin/aurora-terminal-center",root/"usr/local/bin/aurora-terminal-center") if p.is_file() and p.stat().st_mode&0o111),None)
if center:
    (apps/"chimera-terminal-center.desktop").write_text("""[Desktop Entry]
Type=Application
Name=Aurora Terminal Center
Comment=Available terminal emulators and command shells
Exec=aurora-terminal-center
Terminal=false
Icon=chimera-terminal
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
""")
print("Created desktop entries only for audited terminal/shell providers.")
PY
