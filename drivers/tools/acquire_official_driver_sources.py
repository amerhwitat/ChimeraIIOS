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
    if os.path.isdir(os.path.join(dst,".git")):
        subprocess.run(["git","-C",dst,"fetch","--depth=1","origin"],check=False)
        subprocess.run(["git","-C",dst,"reset","--hard","origin/HEAD"],check=False)
    else:
        subprocess.run(["git","clone","--depth=1","--filter=blob:none",url,dst],check=False)
    if os.path.isdir(os.path.join(dst,".git")):
        rev=subprocess.check_output(["git","-C",dst,"rev-parse","HEAD"],text=True).strip()
        rows.append({"name":name,"url":url,"revision":rev})
# Apple DriverKit is an SDK/API reference and is not redistributed by this script.
rows.append({"name":"apple-driverkit","url":"https://developer.apple.com/documentation/driverkit","mode":"reference-only","reason":"Apple SDK, signing and entitlement requirements"})
rows.append({"name":"apple-system-extensions","url":"https://developer.apple.com/documentation/SystemExtensions","mode":"reference-only","reason":"Apple SDK, signing and entitlement requirements"})
with open(os.path.join(ROOT,"manifests","acquired-driver-sources.json"),"w",encoding="utf-8") as f:
    json.dump({"schema":"chimera-acquired-driver-sources-v1","sources":rows},f,indent=2)
print(json.dumps({"acquired":len(rows)}))
