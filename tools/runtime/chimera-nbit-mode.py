#!/usr/bin/env python3
"""Installed entry point for the shared N-bit profile selector."""
import os, runpy, sys
from pathlib import Path

HERE=Path(__file__).resolve()
candidates=[
    HERE.parents[2]/"tools/nbit/select_mode.py",
    Path("/usr/share/chimera/nbit/select_mode.py"),
    Path("/usr/lib/chimera/tools/select_mode.py"),
]
selector=next((p for p in candidates if p.is_file()),None)
if selector is None:
    print("chimera-nbit-mode: selector implementation is not installed",file=sys.stderr)
    raise SystemExit(2)
if "--config" not in sys.argv:
    default=os.environ.get("CHIMERA_NBIT_PROFILE_FILE","/etc/chimera/nbit-mode.json")
    sys.argv.extend(["--config",default])
sys.argv[0]=str(selector)
runpy.run_path(str(selector),run_name="__main__")
