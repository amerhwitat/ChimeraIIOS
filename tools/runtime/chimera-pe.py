#!/usr/bin/env python3
"""Chimera II PE compatibility front-end.

Validates PE32/PE32+ images before handing them to the native Chimera PE
runtime. It deliberately does not treat Wine or SS64 as the native loader.
A native runner is used when present; Wine is an explicit opt-in fallback.
"""
from __future__ import annotations
import os, struct, subprocess, sys
from pathlib import Path

MACHINES={0x14c:"x86",0x8664:"x64",0xaa64:"arm64"}

def inspect(path: Path):
    b=path.read_bytes()
    if len(b)<0x40 or b[:2]!=b"MZ": raise ValueError("not a PE/DOS image")
    peoff=struct.unpack_from("<I",b,0x3c)[0]
    if peoff+24>len(b) or b[peoff:peoff+4]!=b"PE\0\0": raise ValueError("invalid PE signature")
    machine,nsec=struct.unpack_from("<HH",b,peoff+4)
    opt=peoff+24; magic=struct.unpack_from("<H",b,opt)[0]
    if magic not in (0x10b,0x20b): raise ValueError("unsupported PE optional header")
    entry=struct.unpack_from("<I",b,opt+16)[0]
    image_base=struct.unpack_from("<Q",b,opt+24)[0] if magic==0x20b else struct.unpack_from("<I",b,opt+28)[0]
    image_size=struct.unpack_from("<I",b,opt+56)[0]
    chars=struct.unpack_from("<H",b,peoff+22)[0]
    return {"machine":MACHINES.get(machine,"unknown"),"machine_id":machine,"format":"PE32+" if magic==0x20b else "PE32","sections":nsec,"entry_rva":entry,"image_base":image_base,"image_size":image_size,"dll":bool(chars&0x2000)}

def run(path: Path, args):
    meta=inspect(path)
    runner=Path(os.environ.get("CHIMERA_PE_RUNNER","/usr/lib/chimera/win/chimera-pe-runner"))
    if runner.exists() and os.access(runner,os.X_OK):
        return subprocess.call([str(runner),str(path),*args])
    if os.environ.get("CHIMERA_WINDOWS_WINE_FALLBACK") == "1":
        wine=os.environ.get("WINE","wine")
        return subprocess.call([wine,str(path),*args])
    print(f"chimera-pe: validated {meta['format']} {meta['machine']} image, but native PE execution service is not installed.",file=sys.stderr)
    print("Install/build chimera-pe-runner, or explicitly set CHIMERA_WINDOWS_WINE_FALLBACK=1 for an external compatibility backend.",file=sys.stderr)
    return 126

def main(argv):
    if len(argv)<2 or argv[1] in ("-h","--help"):
        print("usage: chimera-pe.py inspect FILE.exe|FILE.dll | run FILE.exe [args...]")
        return 0 if len(argv)>1 else 2
    op=argv[1]; path=Path(argv[2]) if len(argv)>2 else None
    if path is None or not path.is_file(): print("chimera-pe: file not found",file=sys.stderr); return 2
    try: meta=inspect(path)
    except (OSError,ValueError) as e: print(f"chimera-pe: {e}",file=sys.stderr); return 1
    if op=="inspect":
        for k,v in meta.items(): print(f"{k}: {v}")
        return 0
    if op=="run": return run(path,argv[3:])
    print("chimera-pe: unknown operation",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main(sys.argv))
