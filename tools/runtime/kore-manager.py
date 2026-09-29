#!/usr/bin/env python3
"""Compatibility broker for Kore requests.

Native Koronos Kore is authoritative when available. This small user-space
broker exists so systemd-style applications can run in a Linux/Live fallback
where the native kernel service API is not yet exposed to user space.
"""
from __future__ import annotations
import json, os, signal, subprocess, time
from pathlib import Path
ROOT=Path(os.environ.get("CHIMERA_KORE_RUNTIME","/run/kore")); REQ=ROOT/"requests"; STATE=ROOT/"state.json"; UNITS=Path(os.environ.get("CHIMERA_KORE_UNITS","/etc/chimera/kore-units.json")); procs={}

def load_units():
    try:return json.loads(UNITS.read_text(encoding="utf-8")).get("units",{})
    except Exception:return {}

def save(units):
    STATE.parent.mkdir(parents=True,exist_ok=True); out={"units":{}}
    for n,u in units.items():out["units"][n]={"description":u.get("description",n),"state":u.get("state","stopped"),"enabled":u.get("enabled",False),"pid":procs.get(n).pid if n in procs and procs[n].poll() is None else "-","requires":u.get("requires",[]),"wants":u.get("wants",[])}
    STATE.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")

def start(name,units):
    u=units.get(name)
    if not u:return 4
    if name in procs and procs[name].poll() is None:return 0
    cmd=u.get("exec_start")
    if not cmd: u["state"]="running";return 0
    try:procs[name]=subprocess.Popen(cmd,shell=True);u["state"]="running";return 0
    except Exception:u["state"]="failed";return 1

def stop(name,units):
    p=procs.get(name)
    if p and p.poll() is None:p.terminate()
    if name in units:units[name]["state"]="stopped"
    return 0

def main():
    ROOT.mkdir(parents=True,exist_ok=True);REQ.mkdir(parents=True,exist_ok=True);units=load_units();save(units)
    while True:
        for p in list(REQ.iterdir()):
            try:r=json.loads(p.read_text());a=r.get("action");n=r.get("unit")
            except Exception:p.unlink(missing_ok=True);continue
            if a=="start":start(n,units)
            elif a=="stop":stop(n,units)
            elif a=="restart":stop(n,units);start(n,units)
            elif a=="enable" and n in units:units[n]["enabled"]=True
            elif a=="disable" and n in units:units[n]["enabled"]=False
            elif a=="reload":units=load_units()
            p.unlink(missing_ok=True);save(units)
        for n,p in list(procs.items()):
            if p.poll() is not None:units.setdefault(n,{})["state"]="failed";del procs[n];save(units)
        time.sleep(.25)
if __name__=="__main__":main()
