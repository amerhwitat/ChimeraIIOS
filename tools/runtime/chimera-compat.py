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
    # Support both direct invocation (chimera-compat COMMAND ...) and the
    # symlinked command-provider form used by the SS64 compatibility catalog.
    if Path(argv[0]).name == "chimera-compat.py":
        if len(argv)<2:
            return 2
        target=Path(argv[1]); args=argv[2:]
    else:
        target=Path(argv[0]); args=argv[1:]
    if target.suffix.lower() in {".exe", ".dll"} and target.is_file():
        if target.suffix.lower()==".dll":
            return subprocess.call([sys.executable,str(PE_TOOL),"inspect",str(target)])
        return subprocess.call([sys.executable,str(PE_TOOL),"run",str(target),*args])
    name=target.name
    try:
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        data={"commands":{}}
    item=data.get("commands",{}).get(name,{})
    provider=item.get("provider")
    if provider and Path(provider).exists() and provider != str(target):
        return subprocess.call([provider]+args)
    print(f"chimera-compat: {name}: command registered for compatibility, but no runnable provider is staged.", file=sys.stderr)
    print("Use 'chimera search %s' or install the provider package named in the compatibility manifest." % name, file=sys.stderr)
    return 127

if __name__=="__main__": raise SystemExit(main(sys.argv))
