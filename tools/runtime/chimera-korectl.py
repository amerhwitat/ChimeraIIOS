#!/usr/bin/env python3
"""User-space control client for the native Kore service manager.

This is a compatibility boundary, not a second init system. Kore owns service
state and consumes requests from /run/kore/requests.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
STATE = Path(os.environ.get("CHIMERA_KORE_STATE", "/run/kore/state.json"))
REQUESTS = Path(os.environ.get("CHIMERA_KORE_REQUESTS", "/run/kore/requests"))

def load():
    try: return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception: return {"units": {}}

def request(action, unit):
    REQUESTS.mkdir(parents=True, exist_ok=True)
    p = REQUESTS / f"{os.getpid()}-{action}-{unit.replace('/','_')}"
    p.write_text(json.dumps({"action":action,"unit":unit,"uid":getattr(os,"getuid",lambda:0)()})+"\n", encoding="utf-8")

def main(argv):
    args=argv[1:]
    if not args or args[0] in ("help","--help","-h"):
        print("korectl {start|stop|restart|status|enable|disable|is-enabled|list-units|list-dependencies|daemon-reload} UNIT"); return 0
    op=args[0]; data=load(); units=data.get("units",{})
    if op in ("list-units","list"):
        for n,i in sorted(units.items()): print(f"{n}\t{i.get('state','unknown')}")
        return 0
    if op=="list-dependencies":
        if len(args)<2:return 2
        u=units.get(args[1],{}); [print(x) for x in u.get("requires",[])+u.get("wants",[])]; return 0
    if op=="daemon-reload": request("reload","manager"); return 0
    if len(args)<2:return 2
    unit=args[1]
    if op=="status":
        i=units.get(unit)
        if not i: print(f"Unit {unit} could not be found.",file=sys.stderr); return 4
        print(f"● {unit} - {i.get('description',unit)}\n   State: {i.get('state','unknown')}\n   PID: {i.get('pid','-')}")
        return 0 if i.get("state") in ("running","active") else 3
    if op=="is-enabled": return 0 if units.get(unit,{}).get("enabled",False) else 1
    if op in ("start","stop","restart","enable","disable"): request(op,unit); return 0
    print(f"korectl: unsupported operation: {op}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main(sys.argv))
