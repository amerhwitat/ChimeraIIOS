#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
backends=json.loads((ROOT/"tools/virtualization/hypervisor-backends.json").read_text())
profiles=json.loads((ROOT/"tools/virtualization/machine-profiles.json").read_text())
ids={b["id"]:b for b in backends["backends"]}
coverage=json.loads((ROOT/"tools/virtualization/execution-coverage.json").read_text())
dimensions=coverage["dimensions"]
for target in coverage["targets"]:
    for dim in dimensions:
        if type(target.get(dim)) is not bool: raise SystemExit(f"missing boolean {dim} for {target.get('id')}")
    if target["official_conformance_tested"] and not target["executed"]:
        raise SystemExit("conformance cannot pass without execution: "+target["id"])
    if target["guest_boot_tested"] and not target["executed"]:
        raise SystemExit("boot test cannot pass without execution: "+target["id"])
seen=set()
for p in profiles["profiles"]:
    if p["id"] in seen: raise SystemExit("duplicate profile: "+p["id"])
    seen.add(p["id"])
    if p["backend"] not in ids: raise SystemExit("unknown backend: "+p["backend"])
    if p["backend"]=="chimera-nbit" and ids[p["backend"]]["enabled"]:
        raise SystemExit("native N-bit must stay disabled until QEMU integration and boot CI pass")
    if not p["machine"] or not p["cpu"] or not p["devices"]: raise SystemExit("incomplete profile: "+p["id"])
nbit=next(t for t in coverage["targets"] if t["id"]=="chimera-nbit-v0.1")
if nbit["guest_boot_tested"] or nbit["official_conformance_tested"]:
    raise SystemExit("experimental N-bit must not claim guest boot or official conformance")
print(f"profiles valid: {len(seen)}; coverage targets valid: {len(coverage['targets'])}; native N-bit backend remains gated")
