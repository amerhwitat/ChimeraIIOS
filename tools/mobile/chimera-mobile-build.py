#!/usr/bin/env python3
"""Device-aware Chimera II Mobile ROM/ISO builder with Aurora visual media."""
import argparse,hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; PROFILES=ROOT/"mobile/device-profiles"; OUT=ROOT/"build/mobile"
AURORA_BUILDER=ROOT/"tools/aurora/build-visual-assets.sh"
def run(c, timeout=None): return subprocess.run(c,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
def usb_scan():
    out={"usb":{"lsusb":None,"adb_server":None,"adb_devices":[],"fastboot_devices":[]}}
    if shutil.which("lsusb"):
        q=run(["lsusb"]); out["usb"]["lsusb"]=q.stdout.strip()
    if shutil.which("adb"):
        run(["adb","start-server"]); q=run(["adb","devices","-l"]); out["usb"]["adb_server"]="running"
        out["usb"]["adb_devices"]=[x.strip() for x in q.stdout.splitlines()[1:] if x.strip()]
    if shutil.which("fastboot"):
        q=run(["fastboot","devices","-l"]); out["usb"]["fastboot_devices"]=[x.strip() for x in q.stdout.splitlines() if x.strip()]
    return out
def detect(power_on=False, timeout=20):
    run(["adb","start-server"])
    if power_on:
        fp=run(["fastboot","devices"]) if shutil.which("fastboot") else subprocess.CompletedProcess([],0,"")
        if fp.stdout.strip():
            serial=fp.stdout.split()[0]; run(["fastboot","-s",serial,"reboot"],timeout=timeout); run(["adb","wait-for-device"],timeout=timeout)
        else: run(["adb","wait-for-device"],timeout=timeout)
    p=run(["adb","devices"]); ids=[x.split()[0] for x in p.stdout.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=="device"]
    if len(ids)!=1: raise SystemExit(f"expected exactly one authorized Android device, found {len(ids)}")
    s=ids[0]; mp={"manufacturer":"ro.product.manufacturer","model":"ro.product.model","device":"ro.product.device","product":"ro.product.name","board":"ro.product.board","platform":"ro.board.platform","soc":"ro.soc.model","abi":"ro.product.cpu.abilist","android":"ro.build.version.release","bootloader":"ro.bootloader","locked":"ro.boot.flash.locked","verifiedboot":"ro.boot.verifiedbootstate","fingerprint":"ro.build.fingerprint","build_id":"ro.build.id","build_display":"ro.build.display.id","security_patch":"ro.build.version.security_patch","incremental":"ro.build.version.incremental","slot":"ro.boot.slot_suffix","vbmeta_device_state":"ro.boot.vbmeta.device_state"}
    props={k:run(["adb","-s",s,"shell","getprop",v]).stdout.strip() for k,v in mp.items()}; a=props["abi"].lower(); arch="aarch64" if "arm64" in a or "aarch64" in a else "armv7" if "armeabi" in a or "armv7" in a else "x86_64" if "x86_64" in a else "unknown"
    rom={k:props[k] for k in ("android","fingerprint","build_id","build_display","security_patch","incremental","slot","vbmeta_device_state")}
    return {"serial":s,"architecture":arch,"properties":props,"software":rom,"mode":"adb","power_wake_attempted":power_on}
def load(t):
    for f in sorted(PROFILES.glob("*.json")):
        try:p=json.loads(f.read_text())
        except Exception:continue
        m=p.get("match",{}); x=t["properties"]; pairs={"manufacturer":"manufacturer","model":"model","device":"device","product":"product","board":"board","platform":"platform"}
        if all(not m.get(k) or m[k].lower()==x[v].lower() for k,v in pairs.items()) and (not m.get("architecture") or m["architecture"]==t["architecture"]): return p,f
    raise SystemExit("No exact Chimera device profile matches this phone; refusing generic ROM generation.")
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b): h.update(b)
    return h.hexdigest()
def build(t,p,pf):
    OUT.joinpath("artifacts").mkdir(parents=True,exist_ok=True); s=OUT/"staging"/p["id"]; shutil.rmtree(s,ignore_errors=True); s.mkdir(parents=True)
    k=ROOT/"build/koronos/arm64/koronos.elf"
    if not k.exists(): raise SystemExit("ARM64 Koronos build missing: build the mobile kernel first.")
    shutil.copy2(k,s/"koronos.elf"); shutil.copy2(pf,s/"device-profile.json")
    aurora=s/"aurora"; aurora.mkdir()
    if AURORA_BUILDER.exists():
        q=run([str(AURORA_BUILDER),str(aurora)])
        if q.returncode: raise SystemExit(q.stdout)
    else: raise SystemExit("Aurora visual asset builder is missing.")
    manifest={"schema":"CHM-MOBILE-ROM-2","profile":p["id"],"codename":p["codename"],"target":t,"generated_utc":datetime.now(timezone.utc).isoformat(),"policy":p["policy"],"aurora":{"init_video":"aurora/Init.mp4","progress_state":"aurora/progress/state.json","progress_stages":"aurora/progress/stages.json","embedded":True}}
    (s/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); rom=OUT/"artifacts"/f"chimera-mobile-{p['id']}-{stamp}.zip"; iso=OUT/"artifacts"/f"chimera-mobile-{p['id']}-{stamp}.iso"
    with zipfile.ZipFile(rom,"w",zipfile.ZIP_DEFLATED) as z:
        for x in s.rglob("*"):
            if x.is_file(): z.write(x,x.relative_to(s))
    tool=shutil.which("xorriso") or shutil.which("genisoimage")
    if not tool: raise SystemExit("xorriso/genisoimage is required to generate a real installer ISO")
    c=[tool,"-as","mkisofs","-V","CHIMERA-MOBILE","-o",str(iso),str(s)] if Path(tool).name=="xorriso" else [tool,"-V","CHIMERA-MOBILE","-o",str(iso),str(s)]
    q=run(c)
    if q.returncode: raise SystemExit(q.stdout)
    r={"profile":p,"target":t,"rom":str(rom),"iso":str(iso),"rom_sha256":sha(rom),"iso_sha256":sha(iso),"profile_file":str(pf),"aurora":{"init_video":str(s/"aurora/Init.mp4"),"progress_state":str(s/"aurora/progress/state.json")}}
    (OUT/"last-build.json").write_text(json.dumps(r,indent=2)+"\n"); return r
a=argparse.ArgumentParser(); a.add_argument("--detect",action="store_true"); a.add_argument("--usb-scan",action="store_true"); a.add_argument("--build",action="store_true"); a.add_argument("--power-on",action="store_true"); x=a.parse_args()
if x.usb_scan: print(json.dumps(usb_scan(),indent=2)); raise SystemExit(0)
t=detect(power_on=x.power_on); p,pf=load(t); print(json.dumps({"target":t,"profile":p,"profile_file":str(pf)} if not x.build else build(t,p,pf),indent=2))
