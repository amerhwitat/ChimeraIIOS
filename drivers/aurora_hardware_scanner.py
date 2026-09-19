#!/usr/bin/env python3
"""Read-mostly cross-platform hardware/driver inventory and remediation planner."""
from __future__ import annotations
import argparse,hashlib,json,platform,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]; STATE=ROOT/"var"/"aurora-driver-state.json"
def run(cmd):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
        return {"ok":p.returncode==0,"stdout":p.stdout[-12000:],"stderr":p.stderr[-4000:]}
    except Exception as e:return {"ok":False,"error":str(e)}
def collect():
    osname=platform.system().lower()
    out={"timestamp":datetime.now(timezone.utc).isoformat(),"host":{"os":osname,"release":platform.release(),"arch":platform.machine()},"devices":[]}
    if osname=="linux":
        for base in ("/sys/class","/sys/bus/pci/devices","/sys/bus/usb/devices"):
            p=Path(base)
            if p.exists():
                for d in sorted(p.iterdir()):
                    item={"source":str(d)}
                    for k in ("vendor","device","class","modalias","uevent","product","manufacturer"):
                        q=d/k
                        if q.is_file():
                            try:item[k]=q.read_text(errors="replace")[:4000]
                            except OSError:pass
                    if len(item)>1:out["devices"].append(item)
        out["commands"]={"lspci":run(["lspci","-nn"]) if shutil.which("lspci") else None,"lsusb":run(["lsusb"]) if shutil.which("lsusb") else None}
    elif osname=="windows":
        ps="Get-PnpDevice | Select Status,Class,FriendlyName,InstanceId,Manufacturer,ProblemCode | ConvertTo-Json -Depth 3"
        out["devices"]=[{"source":"PowerShell","data":run(["powershell","-NoProfile","-Command",ps])}]
        out["commands"]={"pnputil":run(["pnputil","/enum-drivers"])}
    elif osname=="darwin":
        out["commands"]={"system_profiler":run(["system_profiler","SPHardwareDataType","SPPCIDataType","SPUSBDataType","SPDisplaysDataType"])}
        out["devices"]=[{"source":"ioreg","data":run(["ioreg","-l","-w","0"])}]
    return out
def make_plan(inv):
    return {"generated_at":inv["timestamp"],"host":inv["host"],"policy":{"verify_signature":True,"verify_hash":True,"license_check":True,"quarantine":True,"explicit_apply":True,"rollback":True},"actions":[],"inventory_sha256":hashlib.sha256(json.dumps(inv,sort_keys=True).encode()).hexdigest()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--json",action="store_true");ap.add_argument("--apply",action="store_true");ap.add_argument("--output",default=str(STATE));a=ap.parse_args()
    inv=collect();plan=make_plan(inv);Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps({"inventory":inv,"plan":plan},indent=2))
    if a.json:print(json.dumps({"inventory":inv,"plan":plan,"apply_requested":a.apply},indent=2))
    else:print(f"Aurora hardware scan complete: {len(inv['devices'])} device records; remediation actions={len(plan['actions'])}.")
    if a.apply:print("No native driver was installed: the action plan is empty and the operation is non-destructive.")
if __name__=="__main__":main()
