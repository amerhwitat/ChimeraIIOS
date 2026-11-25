#!/usr/bin/env python3
import json,os,subprocess,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"foreign-source")
os.makedirs(OUT,exist_ok=True)
SOURCES=[
 ("linux","https://github.com/torvalds/linux.git"),
 ("windows-driver-samples","https://github.com/microsoft/Windows-driver-samples.git"),
 ("windows-rust-driver-samples","https://github.com/microsoft/Windows-rust-driver-samples.git"),
]
rows=[]
for name,url in SOURCES:
    dst=os.path.join(OUT,name)
    git_dir=os.path.join(dst,".git")
    if os.path.isdir(git_dir):
        # The upstream Windows driver samples repository marks one INF as
        # working-tree-encoding=UTF-16LE-BOM even though its committed blob is
        # not valid UTF-8. Override that single path locally before checkout;
        # the Git object remains untouched and the source snapshot is still
        # pinned by the recorded commit SHA.
        if name == "windows-driver-samples":
            info=os.path.join(git_dir,"info")
            os.makedirs(info,exist_ok=True)
            with open(os.path.join(info,"attributes"),"w",encoding="utf-8") as f:
                f.write("network/netadaptercx/netvadapter/km/netvadapter.inf -working-tree-encoding\n")
        subprocess.run(["git","-C",dst,"fetch","--depth=1","origin"],check=False)
        subprocess.run(["git","-C",dst,"reset","--hard","origin/HEAD"],check=False)
    else:
        clone=["git","clone","--depth=1","--filter=blob:none"]
        if name == "windows-driver-samples":
            clone.append("--no-checkout")
        clone.extend([url,dst])
        subprocess.run(clone,check=False)
        if name == "windows-driver-samples" and os.path.isdir(git_dir):
            info=os.path.join(git_dir,"info")
            os.makedirs(info,exist_ok=True)
            with open(os.path.join(info,"attributes"),"w",encoding="utf-8") as f:
                f.write("network/netadaptercx/netvadapter/km/netvadapter.inf -working-tree-encoding\n")
            subprocess.run(["git","-C",dst,"checkout","-f","HEAD"],check=False)
    if os.path.isdir(git_dir):
        rev=subprocess.check_output(["git","-C",dst,"rev-parse","HEAD"],text=True).strip()
        rows.append({"name":name,"url":url,"revision":rev})
# Apple DriverKit is an SDK/API reference and is not redistributed by this script.
rows.append({"name":"apple-driverkit","url":"https://developer.apple.com/documentation/driverkit","mode":"reference-only","reason":"Apple SDK, signing and entitlement requirements"})
rows.append({"name":"apple-system-extensions","url":"https://developer.apple.com/documentation/SystemExtensions","mode":"reference-only","reason":"Apple SDK, signing and entitlement requirements"})
with open(os.path.join(ROOT,"manifests","acquired-driver-sources.json"),"w",encoding="utf-8") as f:
    json.dump({"schema":"chimera-acquired-driver-sources-v1","sources":rows},f,indent=2)
print(json.dumps({"acquired":len(rows)}))
