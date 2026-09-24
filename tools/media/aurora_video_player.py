#!/usr/bin/env python3
"""Aurora Video Player entry point using the shared metadata/association model."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from file_associations import resolve
from file_metadata import properties

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("path",type=Path)
    p.add_argument("--info",action="store_true")
    p.add_argument("--enqueue",action="store_true")
    p.add_argument("--subtitle",default=None)
    a=p.parse_args()
    association=resolve(a.path)
    if a.info:
        print(json.dumps({"properties":properties(a.path),"association":association,
                          "subtitle":a.subtitle},ensure_ascii=False,indent=2))
        return 0
    if a.enqueue:
        print(json.dumps({"action":"enqueue","path":str(a.path),"association":association,
                          "subtitle":a.subtitle},ensure_ascii=False))
        return 0
    try:
        from playback import play
        return play(a.path)
    except RuntimeError as exc:
        print(f"Aurora Video Player: {exc}",file=sys.stderr)
        return 127

if __name__=="__main__":
    raise SystemExit(main())
