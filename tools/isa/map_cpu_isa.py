#!/usr/bin/env python3
"""Validate and query the canonical CISC/RISC to C8192/R8192 mapping.

This emits mapping metadata only. It never fabricates a decoder, encoder, binary,
or instruction-level conformance claim.
"""
from __future__ import annotations
import argparse, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
DB=ROOT/"isa"/"isa_database.json"
MAP=ROOT/"isa"/"cpu_isa_target_map.json"
EXPECTED={"CISC":"chimera-c8192","RISC":"chimera-r8192",
          "CISC-extension":"chimera-c8192","RISC-extension":"chimera-r8192"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate(db,mapping):
    db_rows={r[0]:r for r in db["architectures"]}
    map_rows={r["architecture"]:r for r in mapping["architectures"]}
    errors=[]
    if set(db_rows)!=set(map_rows):
        errors.append(f"coverage mismatch: missing={sorted(set(db_rows)-set(map_rows))}, extra={sorted(set(map_rows)-set(db_rows))}")
    for arch,row in db_rows.items():
        mapped=map_rows.get(arch)
        if not mapped: continue
        cls=row[1]
        if mapped["isa_class"]!=cls: errors.append(f"{arch}: class mismatch {mapped['isa_class']} != {cls}")
        target=EXPECTED.get(cls)
        if target and mapped["target"]!=target: errors.append(f"{arch}: {cls} must map to {target}, got {mapped['target']}")
        if mapped["verified_form_count"]!=row[7]: errors.append(f"{arch}: verified form count drift")
        if cls not in EXPECTED and mapped["target"] in ("chimera-c8192","chimera-r8192"):
            errors.append(f"{arch}: {cls} incorrectly forced into scalar CISC/RISC target")
    if mapping["unmapped_count"]!=sum(r["target"]=="unclassified-backend" for r in mapping["architectures"]):
        errors.append("unmapped_count mismatch")
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validate",action="store_true")
    p.add_argument("--arch")
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    db=load(DB); mapping=load(MAP)
    errors=validate(db,mapping)
    if errors:
        print("\n".join(errors),file=sys.stderr); return 1
    if a.arch:
        rows=[r for r in mapping["architectures"] if r["architecture"]==a.arch]
        if not rows: print(f"unknown ISA: {a.arch}",file=sys.stderr); return 2
    else: rows=mapping["architectures"]
    if a.json: print(json.dumps(rows,indent=2))
    else:
        for r in rows: print(f'{r["architecture"]:<20} {r["isa_class"]:<16} -> {r["target"]:<24} {r["lowering"]}')
        print(f'Validated {len(mapping["architectures"])} architecture rows against ISA database {db["version"]}')
    return 0

if __name__=="__main__": raise SystemExit(main())
