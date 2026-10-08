#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
backends=json.loads((ROOT/"tools/virtualization/hypervisor-backends.json").read_text())
profiles=json.loads((ROOT/"tools/virtualization/machine-profiles.json").read_text())
ids={b["id"]:b for b in backends["backends"]}
seen=set()
for p in profiles["profiles"]:
    if p["id"] in seen: raise SystemExit("duplicate profile: "+p["id"])
    seen.add(p["id"])
    if p["backend"] not in ids: raise SystemExit("unknown backend: "+p["backend"])
    if p["backend"]=="chimera-nbit" and ids[p["backend"]]["enabled"]:
        raise SystemExit("native N-bit must stay disabled until QEMU integration and boot CI pass")
    if not p["machine"] or not p["cpu"] or not p["devices"]: raise SystemExit("incomplete profile: "+p["id"])
print(f"profiles valid: {len(seen)}; native N-bit backend remains gated")
