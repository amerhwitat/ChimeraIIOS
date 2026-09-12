#!/usr/bin/env python3
"""Generate a deterministic hardware registry from a CHM-HW JSON catalog.

The input can be enriched from external PCI/USB data by a build step; no network
access is performed by this script itself.
"""
from __future__ import annotations
import json
import pathlib
import sys

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: generate_hardware_registry.py input.json output.json", file=sys.stderr)
        return 64
    src, dst = map(pathlib.Path, sys.argv[1:])
    data = json.loads(src.read_text(encoding="utf-8"))
    data["generated_by"] = "ChimeraIIOS/tools/generate_hardware_registry.py"
    data["deterministic"] = True
    dst.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
