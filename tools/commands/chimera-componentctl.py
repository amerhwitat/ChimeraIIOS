#!/usr/bin/env python3
"""Honest control/diagnostic CLI for Koronos and Chimera services."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

COMPONENTS={
 "aegis":{"unit":"aegis.service","checks":[["auditctl","-s"],["nft","list","ruleset"]]},
 "aurora":{"unit":"aurora-session.service","checks":[["pgrep","-af","aurora-shell"],["pactl","info"]]},
 "jasper":{"unit":"jasper.service","checks":[["grub-mkconfig","--version"],["grub-editenv","list"]]},
 "koronos":{"unit":"koronos.service","checks":[["uname","-a"],["chmctl","status"],["dmesg","--level=err"]]},
 "nucleus":{"unit":"nucleus.service","checks":[["sqlite3","--version"],["ls","-l","/var/lib/chimera/nucleus.db"]]},
 "spitfire":{"unit":"spitfire.service","checks":[["grub-file","--version"],["grub-mkrescue","--version"]]},
 "spotnik":{"unit":"spotnik.service","checks":[["ip","-brief","address"],["ip","route"],["ss","-lntup"]]},
}
def execute(argv):
    if not argv or not shutil.which(argv[0]):
        return {"command":argv,"status":"provider-missing","returncode":127,"output":""}
    try:
        p=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15,check=False)
        return {"command":argv,"status":"ok" if p.returncode==0 else "failed","returncode":p.returncode,"output":p.stdout[-8000:]}
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"command":argv,"status":"error","returncode":127,"output":str(exc)}
def live_status():
    cmdline=Path("/proc/cmdline").read_text(encoding="utf-8",errors="replace") if Path("/proc/cmdline").exists() else ""
    medium=Path("/run/live/medium").exists()
    active=("boot=live" in cmdline) or medium
    return {"component":"live","status":"live" if active else "not-live","boot_cmdline":cmdline.strip(),"live_medium_present":medium}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("component",choices=sorted([*COMPONENTS,"live"]))
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("status");sub.add_parser("diagnose");sub.add_parser("logs")
    sub.add_parser("list")
    for action in ("start","stop","restart","enable","disable"):
        sub.add_parser(action)
    a=p.parse_args()
    if a.component=="live":
        result=live_status()
        print(json.dumps(result,indent=2))
        return 0 if result["status"]=="live" else 3
    info=COMPONENTS[a.component];unit=info["unit"]
    if a.action=="list":
        print(json.dumps({name:row["unit"] for name,row in COMPONENTS.items()},indent=2));return 0
    if a.action=="diagnose":
        results=[execute(cmd) for cmd in info["checks"]]
        print(json.dumps({"component":a.component,"unit":unit,"checks":results},indent=2))
        return 0 if any(x["status"]=="ok" for x in results) else 3
    if a.action=="logs":
        r=execute(["journalctl","-u",unit,"-n","50","--no-pager"])
        print(r["output"],end="")
        return r["returncode"]
    if a.action=="status":
        if not shutil.which("systemctl"):
            print(json.dumps({"component":a.component,"unit":unit,"status":"service-manager-unavailable"}));return 3
        load=execute(["systemctl","show","-p","LoadState","--value",unit])
        state=execute(["systemctl","is-active",unit])
        status=state["output"].strip() if state["status"]=="ok" else "not-active-or-not-installed"
        print(json.dumps({"component":a.component,"unit":unit,"load_state":load["output"].strip(),"status":status},indent=2))
        return 0 if status=="active" else 3
    if not shutil.which("systemctl"):
        print("chimera-componentctl: systemctl is unavailable",file=sys.stderr);return 127
    unit_file=execute(["systemctl","show","-p","LoadState","--value",unit])
    if unit_file["output"].strip() in ("not-found",""):
        print(f"chimera-componentctl: {unit} is not installed; refusing to report a successful action",file=sys.stderr);return 3
    r=execute(["systemctl",a.action,unit])
    print(r["output"],end="")
    return r["returncode"]
if __name__=="__main__": raise SystemExit(main())
