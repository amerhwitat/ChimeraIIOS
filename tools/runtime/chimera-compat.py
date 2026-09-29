#!/usr/bin/env python3
"""Dispatcher used for commands registered by the SS64 compatibility scan.

If a real binary was staged by the build it is executed. Otherwise the command
is reported as registered-but-provider-missing; SS64 is a reference source and
is never treated as a binary distribution.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(os.environ.get("CHIMERA_COMPAT_ROOT", "/usr/lib/chimera/compat"))
MANIFEST=Path(os.environ.get("CHIMERA_COMPAT_MANIFEST", str(ROOT/"commands.json")))

def main(argv):
    name=Path(argv[0]).name
    try: data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception: data={"commands":{}}
    item=data.get("commands",{}).get(name,{})
    provider=item.get("provider")
    if provider and Path(provider).exists() and provider != argv[0]:
        return subprocess.call([provider]+argv[1:])
    print(f"chimera-compat: {name}: command registered for compatibility, but no runnable provider is staged.", file=sys.stderr)
    print("Use 'chimera search %s' or install the provider package named in the compatibility manifest." % name, file=sys.stderr)
    return 127
if __name__=="__main__": raise SystemExit(main(sys.argv))
