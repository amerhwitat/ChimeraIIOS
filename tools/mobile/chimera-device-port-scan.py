#!/usr/bin/env python3
"""Chimera II OS universal host-port/device scanner.

Read-only inventory of devices visible through Linux USB, udev/sysfs, ADB,
Fastboot, libimobiledevice, MTP, serial/USB-serial, and Thunderbolt/USB4.
It never opens a raw block device and never writes to a connected phone.
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, glob
from datetime import datetime, timezone
from pathlib import Path

def run(cmd, timeout=8):
    try:
        return subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout).stdout.strip()
    except Exception:
        return ""

def have(x): return shutil.which(x) is not None

def usb_inventory():
    rows=[]
    if have("lsusb"):
        out=run(["lsusb"])
        for line in out.splitlines():
            m=re.match(r"Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)",line)
            if m:
                rows.append({"bus":m.group(1),"device":m.group(2),"vid":m.group(3).lower(),
                             "pid":m.group(4).lower(),"description":m.group(5).strip()})
            elif line.strip():
                rows.append({"raw":line})
    return rows

def udev_details():
    out=[]
    for dev in glob.glob("/sys/bus/usb/devices/*"):
        name=os.path.basename(dev)
        if ":" in name or not os.path.isdir(dev): continue
        def read(n):
            try:return Path(dev,n).read_text().strip()
            except:return ""
        vid,pid=read("idVendor"),read("idProduct")
        if not vid or not pid: continue
        out.append({"sysfs":dev,"vid":vid.lower(),"pid":pid.lower(),
                    "manufacturer":read("manufacturer"),"product":read("product"),
                    "serial":read("serial"),"busnum":read("busnum"),"devnum":read("devnum"),
                    "speed":read("speed")})
    return out

def adb():
    if not have("adb"): return []
    run(["adb","start-server"])
    out=run(["adb","devices","-l"])
    rows=[]
    for line in out.splitlines()[1:]:
        if not line.strip(): continue
        p=line.split()
        if len(p)>=2:
            rows.append({"transport":"adb","id":p[0],"state":p[1],"details":" ".join(p[2:])})
    return rows

def fastboot():
    if not have("fastboot"): return []
    out=run(["fastboot","devices","-l"])
    return [{"transport":"fastboot","id":p[0],"details":" ".join(p[1:])}
            for p in (x.split() for x in out.splitlines()) if p]

def apple():
    if not have("idevice_id"): return []
    ids=run(["idevice_id","-l"])
    rows=[]
    for ident in ids.splitlines():
        if not ident.strip(): continue
        info={}
        if have("ideviceinfo"):
            raw=run(["ideviceinfo","-u",ident],timeout=15)
            for line in raw.splitlines():
                if ": " in line:
                    k,v=line.split(": ",1); info[k]=v
        rows.append({"transport":"usbmuxd/libimobiledevice","id":ident,
                     "model":info.get("ProductType",""),"os_version":info.get("ProductVersion",""),
                     "name":info.get("DeviceName",""),"serial":info.get("SerialNumber","")})
    return rows

def serial_ports():
    paths=sorted(set(glob.glob("/dev/ttyUSB*")+glob.glob("/dev/ttyACM*")+glob.glob("/dev/ttyS*")))
    return [{"path":p,"transport":"serial/usb-serial"} for p in paths]

def mtp():
    rows=[]
    if have("gio"):
        out=run(["gio","mount","-l"])
        for line in out.splitlines():
            if "mtp://" in line.lower() or "gphoto2://" in line.lower():
                rows.append({"transport":"mtp/gphoto2","description":line.strip()})
    return rows

def thunderbolt():
    rows=[]
    base=Path("/sys/bus/thunderbolt/devices")
    if base.exists():
        for d in base.iterdir():
            if d.is_dir():
                def r(n):
                    try:return (d/n).read_text().strip()
                    except:return ""
                rows.append({"transport":"thunderbolt/usb4","path":str(d),
                             "vendor":r("vendor_name"),"device":r("device_name"),
                             "authorized":r("authorized")})
    return rows

def windows_hint():
    return {"windows_host_note":"Run tools/mobile/chimera-device-port-scan.ps1 on native Windows. WSL can only see USB devices passed through by usbipd/WSLg."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    data={"schema":"CHM-HOST-PORT-INVENTORY-1",
          "timestamp":datetime.now(timezone.utc).isoformat(),
          "host":{"os":run(["uname","-a"]) if have("uname") else "",
                  "usb_tools":{x:have(x) for x in ["lsusb","udevadm","adb","fastboot","idevice_id","ideviceinfo","gio"]}},
          "usb_devices":usb_inventory(),
          "udev_usb_devices":udev_details(),
          "android_adb":adb(),
          "android_fastboot":fastboot(),
          "apple_usbmux":apple(),
          "mtp_or_gphoto2":mtp(),
          "serial_ports":serial_ports(),
          "thunderbolt_usb4":thunderbolt(),
          "windows":windows_hint()}
    print(json.dumps(data,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
