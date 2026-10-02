#!/usr/bin/env python3
"""Device-aware Chimera II Mobile ROM/ISO builder."""
import argparse,hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; PROFILES=ROOT/"mobile/device-profiles"; OUT=ROOT/"build/mobile"
def run(c): return subprocess.run(c,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def detect():
    run(["adb","start-server"]); p=run(["adb","devices"])
    ids=[x.split()[0] for x in p.stdout.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=="device"]
    if len(ids)!=1: raise SystemExit(f"expected exactly one authorized Android device, found {len(ids)}")
    s=ids[0]; mp={"manufacturer":"ro.product.manufacturer","model":"ro.product.model","device":"ro.product.device","product":"ro.product.name","board":"ro.product.board","platform":"ro.board.platform","soc":"ro.soc.model","abi":"ro.product.cpu.abilist","android":"ro.build.version.release","bootloader":"ro.bootloader","locked":"ro.boot.flash.locked","verifiedboot":"ro.boot.verifiedbootstate"}
    props={k:run(["adb","-s",s,"shell","getprop",v]).stdout.strip() for k,v in mp.items()}
    a=props["abi"].lower(); arch="aarch64" if "arm64" in a or "aarch64" in a else "armv7" if "armeabi" in a or "armv7" in a else "x86_64" if "x86_64" in a else "unknown"
    return {"serial":s,"architecture":arch,"properties":props}
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
        for b in iter(lambda:f.read(1048576),b):h.update(b)
    return h.hexdigest()
def build(t,p,pf):
    OUT.joinpath("artifacts").mkdir(parents=True,exist_ok=True); s=OUT/"staging"/p["id"]; shutil.rmtree(s,ignore_errors=True); s.mkdir(parents=True)
    k=ROOT/"build/koronos/arm64/koronos.elf"
    if not k.exists(): raise SystemExit("ARM64 Koronos build missing: build the mobile kernel first.")
    shutil.copy2(k,s/"koronos.elf"); shutil.copy2(pf,s/"device-profile.json")
    manifest={"schema":"CHM-MOBILE-ROM-1","profile":p["id"],"codename":p["codename"],"target":t,"generated_utc":datetime.now(timezone.utc).isoformat(),"policy":p["policy"]}
    (s/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); rom=OUT/"artifacts"/f"chimera-mobile-{p['id']}-{stamp}.zip"; iso=OUT/"artifacts"/f"chimera-mobile-{p['id']}-{stamp}.iso"
    with zipfile.ZipFile(rom,"w",zipfile.ZIP_DEFLATED) as z:
        for x in s.iterdir(): z.write(x,x.name)
    tool=shutil.which("xorriso") or shutil.which("genisoimage")
    if not tool: raise SystemExit("xorriso/genisoimage is required to generate a real installer ISO")
    c=[tool,"-as","mkisofs","-V","CHIMERA-MOBILE","-o",str(iso),str(s)] if Path(tool).name=="xorriso" else [tool,"-V","CHIMERA-MOBILE","-o",str(iso),str(s)]
    q=run(c)
    if q.returncode: raise SystemExit(q.stdout)
    r={"profile":p,"target":t,"rom":str(rom),"iso":str(iso),"rom_sha256":sha(rom),"iso_sha256":sha(iso),"profile_file":str(pf)}
    (OUT/"last-build.json").write_text(json.dumps(r,indent=2)+"\n"); return r
a=argparse.ArgumentParser(); a.add_argument("--detect",action="store_true"); a.add_argument("--build",action="store_true"); x=a.parse_args()
t=detect(); p,pf=load(t); print(json.dumps({"target":t,"profile":p,"profile_file":str(pf)} if not x.build else build(t,p,pf),indent=2))
