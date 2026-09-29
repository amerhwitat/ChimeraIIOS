#!/usr/bin/env python3
"""Chimera compatibility dispatcher for native commands and Windows PE files."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path(os.environ.get("CHIMERA_COMPAT_ROOT", "/usr/lib/chimera/compat"))
MANIFEST=Path(os.environ.get("CHIMERA_COMPAT_MANIFEST", str(ROOT/"commands.json")))
PE_TOOL=Path(os.environ.get("CHIMERA_PE_TOOL", "/usr/bin/chimera-pe.py"))

def main(argv):
    if not argv:
        return 2
    target=Path(argv[0])
    # A PE image supplied directly to the compatibility dispatcher is handed
    # to the Windows compatibility boundary. DLLs are loadable modules and
    # are intentionally not treated as directly executable processes.
    if target.suffix.lower() in {".exe", ".dll"} and target.is_file():
        if target.suffix.lower()==".dll":
            return subprocess.call([sys.executable,str(PE_TOOL),"inspect",str(target)])
        return subprocess.call([sys.executable,str(PE_TOOL),"run",str(target),*argv[1:]])
    name=target.name
    try:
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        data={"commands":{}}
    item=data.get("commands",{}).get(name,{})
    provider=item.get("provider")
    if provider and Path(provider).exists() and provider != argv[0]:
        return subprocess.call([provider]+argv[1:])
    print(f"chimera-compat: {name}: command registered for compatibility, but no runnable provider is staged.", file=sys.stderr)
    print("Use 'chimera search %s' or install the provider package named in the compatibility manifest." % name, file=sys.stderr)
    return 127

if __name__=="__main__": raise SystemExit(main(sys.argv[1:]))
