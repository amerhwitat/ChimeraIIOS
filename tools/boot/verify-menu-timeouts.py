#!/usr/bin/env python3
"""Fail CI if any GRUB/Jasper/Spit Fire menu can default before five minutes."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument("--minimum",type=int,default=300);a=ap.parse_args()
    failures=[];checked=[]
    for p in sorted((a.root/"boot").rglob("*.cfg")):
        text=p.read_text(encoding="utf-8",errors="replace")
        if not re.search(r"^\s*menuentry\b",text,re.M):continue
        timeout=re.search(r"^\s*set\s+timeout\s*=\s*(\d+)",text,re.M)
        style=re.search(r"^\s*set\s+timeout_style\s*=\s*menu\s*$",text,re.M)
        default=re.search(r"^\s*set\s+default\s*=",text,re.M)
        checked.append(str(p.relative_to(a.root)))
        if not timeout or int(timeout.group(1))<a.minimum:failures.append(f"{p}: timeout must be >= {a.minimum}s")
        if not style:failures.append(f"{p}: timeout_style=menu is required")
        if not default:failures.append(f"{p}: explicit default item is required")
    gates=a.root/"desktop/aurora/gates_menu.json"
    data=json.loads(gates.read_text(encoding="utf-8"))
    behavior=data.get("menu_behavior",{})
    if int(behavior.get("timeout_seconds",0))<a.minimum:failures.append(f"{gates}: timeout_seconds must be >= {a.minimum}")
    if behavior.get("timeout_mode")!="interactive":failures.append(f"{gates}: timeout_mode must be interactive")
    if behavior.get("default_item")!=0:failures.append(f"{gates}: default_item must be 0")
    print(json.dumps({"checked_grub_menus":checked,"gates_timeout_seconds":behavior.get("timeout_seconds"),"minimum_seconds":a.minimum,"failures":failures},indent=2))
    return 1 if failures else 0
if __name__=="__main__":raise SystemExit(main())
