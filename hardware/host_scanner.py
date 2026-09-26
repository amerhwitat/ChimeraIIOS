#!/usr/bin/env python3
import json,os,platform,subprocess,shutil,datetime

def run(cmd):
    try:return subprocess.run(cmd,capture_output=True,text=True,timeout=15).stdout[:200000]
    except Exception:return ""

def linux_block_inventory():
    raw=run(["lsblk","-J","-o","NAME,KNAME,PATH,TYPE,SIZE,PHY-SEC,LOG-SEC,MIN-IO,OPT-IO,ROTA,TRAN,FSTYPE,MOUNTPOINTS,MODEL"])
    try:return json.loads(raw).get("blockdevices",[])
    except Exception:return []

def scan():
    osname=platform.system()
    out={"schema":"chimera-hardware-inventory-v2","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "host":{"os":osname,"release":platform.release(),"machine":platform.machine(),"python":platform.python_version(),
                 "page_size":getattr(os,"sysconf",lambda *_:4096)("SC_PAGE_SIZE") if hasattr(os,"sysconf") else 4096},
         "devices":[],"storage":[]}
    if osname=="Linux":
        out["host"]["dmi"]=run(["dmidecode","-t","system"]) if shutil.which("dmidecode") else ""
        if shutil.which("lspci"): out["devices"].append({"class":"pci","raw":run(["lspci","-Dnnk"])})
        if shutil.which("lsusb"): out["devices"].append({"class":"usb","raw":run(["lsusb","-nn"])})
        out["devices"].append({"class":"sysfs","entries":os.listdir("/sys/devices")[:1000] if os.path.isdir("/sys/devices") else []})
        out["storage"]=linux_block_inventory()
    elif osname=="Windows":
        ps=shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            out["devices"].append({"class":"pnp","raw":run([ps,"-NoProfile","-Command","Get-PnpDevice | Select Status,Class,FriendlyName,InstanceId | ConvertTo-Json -Depth 4"])})
            out["host"]["computer"]=run([ps,"-NoProfile","-Command","Get-CimInstance Win32_ComputerSystem | ConvertTo-Json -Depth 4"])
    elif osname=="Darwin":
        out["devices"].append({"class":"system_profiler","raw":run(["system_profiler","SPHardwareDataType","SPPCIDataType","SPUSBDataType","SPDisplaysDataType","SPNetworkDataType"])})
        out["devices"].append({"class":"ioreg","raw":run(["ioreg","-l"])})
    return out

if __name__=="__main__":
    print(json.dumps(scan(),indent=2))
