#!/usr/bin/env python3
"""Kore: declarative systemd-like service dependency planner."""
import argparse,json
from pathlib import Path
REG=Path(__file__).resolve().parents[2]/"services"/"registry.json"
def load():return json.loads(REG.read_text()) if REG.exists() else {"services":[]}
def topo(items):
    by={x["name"]:x for x in items};seen=set();order=[]
    def visit(n,stack):
        if n in stack:raise ValueError("service dependency cycle: "+n)
        if n in seen:return
        stack.add(n)
        for d in by.get(n,{}).get("after",[]):visit(d,stack)
        stack.remove(n);seen.add(n);order.append(n)
    for n in by:visit(n,set())
    return [by[n] for n in order]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",choices=["list","plan"]);a=ap.parse_args()
    ordered=topo(load().get("services",[]))
    if a.command=="list":
        for s in ordered:print(f'{s["name"]}\t{s.get("description","")}\t{s.get("enabled",False)}')
    else:print(json.dumps({"start_order":[s["name"] for s in ordered],"manager":"kore","native_adapters":["systemd","launchd","windows-service","chimera"]},indent=2))
if __name__=="__main__":main()
