#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path

STATE = Path(os.environ.get("CHIMERA_NEURAL_STATE", str(Path.home()/".config/chimera/neural-dimension.json")))
DIMENSIONS = (128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)
REPRESENTATIONS = ("HyperDimensional", "Tensor", "Hybrid")

def default():
    return {"dimensions": 1024, "representation": "HyperDimensional",
            "learning": "AdaptiveTensor", "status": "LIVE", "updated": int(time.time())}

def read():
    try:
        d = json.loads(STATE.read_text())
        if d.get("dimensions") in DIMENSIONS and d.get("representation") in REPRESENTATIONS:
            return d
    except Exception:
        pass
    d = default()
    write(d)
    return d

def write(d):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2) + "\n")
    tmp.replace(STATE)

def set_dimension(dimensions, representation=None):
    if dimensions not in DIMENSIONS:
        raise ValueError("unsupported neural dimensionality")
    d = read()
    d["dimensions"] = dimensions
    if representation:
        if representation not in REPRESENTATIONS:
            raise ValueError("unsupported representation")
        d["representation"] = representation
    d["updated"] = int(time.time())
    d["status"] = "LIVE"
    write(d)
    print(json.dumps(d))
    return 0

def main():
    d = read()
    if len(sys.argv) == 1 or sys.argv[1] in ("get", "status"):
        print(json.dumps(d)); return 0
    if sys.argv[1] in ("up", "down"):
        i = DIMENSIONS.index(d["dimensions"])
        i = min(len(DIMENSIONS)-1, i+1) if sys.argv[1] == "up" else max(0, i-1)
        return set_dimension(DIMENSIONS[i], d["representation"])
    if sys.argv[1] == "set" and len(sys.argv) in (3,4):
        return set_dimension(int(sys.argv[2]), sys.argv[3] if len(sys.argv) == 4 else None)
    print("usage: status|get|set DIMENSIONS [HyperDimensional|Tensor|Hybrid]|up|down", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
