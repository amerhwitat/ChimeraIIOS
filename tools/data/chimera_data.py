#!/usr/bin/env python3
"""Chimera II OS data-platform discovery and diagnostics CLI."""
import argparse, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRIES = {
    "databases": ROOT / "data/registry/databases.json",
    "hadoop": ROOT / "data/registry/hadoop.json",
    "openstack": ROOT / "data/registry/openstack.json",
}

def load(name):
    with REGISTRIES[name].open(encoding="utf-8") as f:
        return json.load(f)

def providers():
    rows=[]
    db=load("databases")
    rows.extend({**x,"registry":"databases","available":bool(shutil.which(x["binary"]))} for x in db["engines"])
    hd=load("hadoop")
    rows.extend({**x,"registry":"hadoop","available":bool(shutil.which(x["binary"]))} for x in hd["components"])
    os=load("openstack")
    for x in os["services"]:
        rows.append({**x,"registry":"openstack","binary":"openstack","available":bool(shutil.which("openstack"))})
    return rows

def main():
    ap=argparse.ArgumentParser(prog="chimera-data")
    ap.add_argument("--json",action="store_true")
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    sub.add_parser("providers")
    info=sub.add_parser("info"); info.add_argument("name")
    sub.add_parser("doctor")
    args=ap.parse_args(); rows=providers()
    if args.cmd in ("list","providers"):
        print(json.dumps(rows,indent=2) if args.json else "\n".join(f"{r['id']}: {'available' if r['available'] else 'not installed'} ({r.get('role','')})" for r in rows)); return
    if args.cmd=="info":
        matches=[r for r in rows if r["id"]==args.name]
        print(json.dumps(matches,indent=2)); return
    missing=[r["id"] for r in rows if not r["available"]]
    result={"ok":True,"checked":len(rows),"missing":missing,"note":"Discovery is read-only; install through an explicit package/provider command."}
    print(json.dumps(result,indent=2) if args.json else f"checked={len(rows)} missing={len(missing)}")

if __name__=="__main__": main()
