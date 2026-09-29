#!/usr/bin/env python3
"""systemctl-compatible frontend backed by native Kore.

Supports the common service-management surface without requiring systemd PID 1.
Unknown options are rejected rather than silently emulated.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
KORE=os.environ.get("CHIMERA_KORECTL","/usr/bin/korectl")
import subprocess

def main(argv):
    args=argv[1:]
    if not args or args[0] in ("--help","help","-h"):
        print("systemctl (Chimera compatibility) start|stop|restart|status|enable|disable|is-enabled|list-units|list-dependencies|daemon-reload UNIT"); return 0
    # systemctl commonly accepts flags before the verb; support the safe subset.
    while args and args[0].startswith("-"):
        if args[0] in ("--no-pager","--quiet","--no-legend"): args.pop(0); continue
        if args[0] in ("--system",): args.pop(0); continue
        print(f"systemctl: unsupported option {args[0]}", file=sys.stderr); return 2
    if not args:return 2
    return subprocess.call([KORE]+args)
if __name__=="__main__": raise SystemExit(main(sys.argv))
