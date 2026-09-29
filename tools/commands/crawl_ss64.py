#!/usr/bin/env python3
"""Crawl SS64 indexes and reconcile commands with Chimera II OS.

SS64 is a command-reference/index source only. This tool never copies SS64
prose and never treats SS64 as a binary distributor. Existing target-rootfs
binaries are staged as compatibility providers; missing commands are registered
as native compatibility entries and receive a dispatcher shim.
"""
from __future__ import annotations
import argparse, html.parser, json, os, re, shutil, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
INDEXES={"linux_bash":"https://ss64.com/bash/","macos":"https://ss64.com/mac/","windows_cmd":"https://ss64.com/nt/","powershell":"https://ss64.com/ps/","vbscript":"https://ss64.com/vb/","sql_server":"https://ss64.com/sql/","access":"https://ss64.com/access/","tools":"https://ss64.com/tools/"}
UA="ChimeraIIOS-SS64-Catalog/4.2 (+https://github.com/amerhwitat/ChimeraIIOS)"
class P(html.parser.HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.links=[]; self.a=False; self.h=""; self.t=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a": self.a=True; self.h=dict(attrs).get("href",""); self.t=[]
    def handle_data(self,data):
        if self.a:self.t.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.a:self.links.append((" ".join("".join(self.t).split()),self.h)); self.a=False

def fetch(url,timeout,retries):
    for n in range(retries+1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=timeout) as r:return r.read().decode("utf-8","replace")
        except (urllib.error.URLError,TimeoutError,OSError):
            if n<retries:time.sleep(.25*(n+1))
    raise RuntimeError(url)

def crawl(seed,platform,max_pages,timeout,retries,delay):
    p=urllib.parse.urlparse(seed);prefix=p.path.rstrip("/")+"/";q=[seed];queued={seed};seen=set();out={};failures=0
    while q and len(seen)<max_pages:
        u=q.pop(0)
        if u in seen:continue
        x=urllib.parse.urlparse(u)
        if x.netloc!=p.netloc or not x.path.startswith(prefix):continue
        seen.add(u)
        try:html=fetch(u,timeout,retries)
        except Exception as e:failures+=1;print(f"[WARN] {platform}: {e}");continue
        parser=P();parser.feed(html)
        for label,href in parser.links:
            if not href or href.startswith(("#","javascript:","mailto:")):continue
            a=urllib.parse.urljoin(u,href).split("#",1)[0];t=urllib.parse.urlparse(a)
            if t.netloc!=p.netloc or not t.path.startswith(prefix):continue
            if a not in seen and a not in queued:q.append(a);queued.add(a)
            label=re.sub(r"\s+"," ",label).strip();label=re.sub(r"\s*[•▫]+\s*$","",label).strip()
            if not label or len(label)>160 or len(label)==1 or label in {"Home","Search","Contact","About","Donate","Examples","Syntax","Related","Next","Previous","Back","Top","Index","More"}:continue
            if re.search(r"[A-Za-z0-9_$?&./+:-]",label):out[(label.casefold(),a)]={"name":label,"platform":platform,"source":a}
        if delay:time.sleep(delay)
    return sorted(out.values(),key=lambda x:(x["name"].casefold(),x["source"])),len(seen),failures

def flatten_native(c):
    n=c.get("native_chimera",[])
    if isinstance(n,dict):n=n.get("commands",[])
    return set(n or [])

def rootfs_provider(rootfs,name):
    for p in (rootfs/"usr/bin"/name,rootfs/"bin"/name,rootfs/"usr/sbin"/name,rootfs/"sbin"/name,rootfs/"usr/local/bin"/name):
        if p.is_file() and os.access(p,os.X_OK):return p
    return None

def install_source(repo_root,rootfs,src,dst,mode=0o755):
    s=repo_root/src;d=rootfs/dst
    if not s.exists():return False
    d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d);d.chmod(mode);return True

def reconcile(catalog,rootfs,repo_root):
    cmdlist=repo_root/"system/commands/chimera-command-list.json"
    try:native_doc=json.loads(cmdlist.read_text(encoding="utf-8"))
    except Exception:native_doc={}
    native=flatten_native(native_doc);entries=[]
    for data in catalog["platforms"].values():entries.extend(data.get("commands",[]))
    linux=[x for x in entries if x["platform"]=="linux_bash"]
    compat_root=rootfs/"usr/lib/chimera/compat";compat_bin=compat_root/"bin";compat_bin.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"CHM-COMPAT-1","source":"SS64 command indexes","policy":"Reference names only; providers come from Chimera rootfs or official packages.","commands":{}}
    for x in linux:
        name=x["name"]
        if not re.match(r"^[A-Za-z0-9_.+-]+$",name):continue
        p=rootfs_provider(rootfs,name);item={"name":name,"platform":"linux_bash","source":x["source"],"native_registered":name in native,"provider":"","mode":"registered"}
        if p:
            dst=compat_bin/name
            if not dst.exists():
                try:shutil.copy2(p,dst);dst.chmod(0o755)
                except OSError:pass
            item["provider"]=str(dst);item["mode"]="rootfs-binary"
        else:item["mode"]="native-compat-shim";native.add(name)
        manifest["commands"][name]=item
    for src_name,dst_name in (("tools/runtime/chimera-korectl.py","korectl"),("tools/runtime/chimera-systemctl.py","systemctl"),("tools/runtime/chimera-service.py","service"),("tools/runtime/chimera-compat.py","chimera-compat"),("tools/runtime/kore-manager.py","kore-manager")):
        install_source(repo_root,rootfs,src_name,"usr/bin/"+dst_name)
    install_source(repo_root,rootfs,"tools/runtime/kore-manager.py","usr/libexec/chimera/kore-manager")
    units=repo_root/"system/services/kore-units.json"
    if units.exists():install_source(repo_root,rootfs,"system/services/kore-units.json","etc/chimera/kore-units.json",0o644)
    unit=repo_root/"system/services/kore.service"
    if unit.exists():
        install_source(repo_root,rootfs,"system/services/kore.service","usr/lib/systemd/system/kore.service",0o644)
        w=rootfs/"etc/systemd/system/multi-user.target.wants/kore.service";w.parent.mkdir(parents=True,exist_ok=True)
        try:w.symlink_to("/usr/lib/systemd/system/kore.service")
        except FileExistsError:pass
    for name in sorted(native):
        shim=rootfs/"usr/bin"/name
        if shim.exists():continue
        if re.match(r"^[A-Za-z0-9_.+-]+$",name):
            try:shim.symlink_to("chimera-compat")
            except FileExistsError:pass
    (compat_root/"commands.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    native_doc.setdefault("native_chimera",{})
    if isinstance(native_doc["native_chimera"],dict):
        native_doc["native_chimera"]["commands"]=sorted(native)
        native_doc["native_chimera"]["compatibility_policy"]="Missing SS64-indexed commands are registered as native compatibility entries; runnable binaries are staged only from the Chimera rootfs or official package providers."
        native_doc["native_chimera"]["systemd_compatibility"]=["systemctl","service","korectl","kore.service","systemd target names mapped to Kore targets/services"]
    cmdlist.write_text(json.dumps(native_doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="system/commands/ss64-command-catalog.json");ap.add_argument("--max-pages",type=int,default=3000);ap.add_argument("--timeout",type=float,default=30);ap.add_argument("--retries",type=int,default=2);ap.add_argument("--delay",type=float,default=.05);ap.add_argument("--platforms",nargs="*",choices=sorted(INDEXES));args=ap.parse_args()
    root=Path(__file__).resolve().parents[2];selected=args.platforms or list(INDEXES);catalog={"schema_version":"4.2","product":"Chimera II OS","source":"SS64","source_index":"https://ss64.com/","generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"policy":"Command names, classifications and source URLs only; SS64 prose is not redistributed and SS64 is not treated as a binary distributor.","platforms":{}}
    for platform in selected:
        items,pages,failures=crawl(INDEXES[platform],platform,max(1,args.max_pages),args.timeout,max(0,args.retries),max(0,args.delay));catalog["platforms"][platform]={"index":INDEXES[platform],"pages_crawled":pages,"fetch_failures":failures,"command_count":len(items),"commands":items};print(f"{platform}: {len(items)} commands across {pages} pages ({failures} failures)")
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rootfs=Path(os.environ.get("CHIMERA_ROOTFS_DIR",str(root/"build/iso/rootfs")))
    if rootfs.exists():m=reconcile(catalog,rootfs,root);print(f"Reconciled {len(m['commands'])} Linux/Bash commands; Kore/systemd compatibility staged into {rootfs}")
    return 0
if __name__=="__main__":raise SystemExit(main())
