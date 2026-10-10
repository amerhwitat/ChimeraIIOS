#!/usr/bin/env python3
"""Refresh PCI/USB ID metadata and recursively index trusted upstream driver paths.

This tool downloads metadata/source indexes only. It never downloads, compiles, installs,
or executes driver code. Review licenses and validate hardware compatibility before porting.
"""
import argparse, hashlib, json, pathlib, sys, urllib.error, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
CACHE=ROOT/"data/drivers/upstream"
MAX_BYTES=32*1024*1024
SOURCES={"pci.ids":"https://raw.githubusercontent.com/pciutils/pciids/master/pci.ids","usb.ids":"https://raw.githubusercontent.com/usbutils/usbutils/master/usb.ids"}
TREES={"linux-kernel":("torvalds/linux","master"),"edk2":("tianocore/edk2","master"),"zephyr":("zephyrproject-rtos/zephyr","main")}
PREFIXES=("drivers/net/","drivers/usb/","drivers/ata/","drivers/nvme/","drivers/gpu/","drivers/virtio/","drivers/block/","drivers/hwmon/","drivers/media/","drivers/input/","drivers/sound/","MdeModulePkg/","NetworkPkg/","UsbPkg/","drivers/")
def fetch(url, limit=MAX_BYTES):
 req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-driver-catalog-sync/1.0"})
 with urllib.request.urlopen(req,timeout=30) as response:
  if response.status!=200: raise RuntimeError("upstream HTTP status %s: %s"%(response.status,url))
  data=response.read(limit+1)
 if len(data)>limit: raise RuntimeError("refusing oversized response: "+url)
 return data
def refresh_ids():
 CACHE.mkdir(parents=True,exist_ok=True); report={}
 for filename,url in SOURCES.items():
  data=fetch(url); target=CACHE/filename; target.write_bytes(data)
  report[filename]={"url":url,"path":target.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"status":"downloaded-metadata-unreviewed"}
  print("synced %s: %s bytes sha256=%s"%(filename,len(data),report[filename]["sha256"]))
 return report
def recursive_source_index():
 result={}
 for source_id,(repo,branch) in TREES.items():
  url="https://api.github.com/repos/%s/git/trees/%s?recursive=1"%(repo,branch)
  payload=json.loads(fetch(url).decode("utf-8")); paths=[]
  for item in payload.get("tree",[]):
   path=item.get("path","")
   if item.get("type")=="blob" and path.startswith(PREFIXES) and path.lower().endswith((".c",".h",".cpp",".rs",".yaml",".yml",".dts",".dtsi")): paths.append(path)
  result[source_id]={"repository":"https://github.com/"+repo,"branch":branch,"path_count":len(paths),"truncated":bool(payload.get("truncated",False)),"paths":sorted(paths),"status":"source-path-index-only"}
  print("indexed %s: %s paths; truncated=%s"%(source_id,len(paths),payload.get("truncated",False)))
 return result
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--ids-only",action="store_true");parser.add_argument("--output",type=pathlib.Path,help="output JSON report (default build/driver-source-index.json)");args=parser.parse_args()
 try: ids=refresh_ids();sources={} if args.ids_only else recursive_source_index()
 except (OSError,urllib.error.URLError,UnicodeError,json.JSONDecodeError,RuntimeError) as exc: print("driver catalog sync failed: %s"%exc,file=sys.stderr);return 2
 report={"schema":"CHIMERA-UPSTREAM-DRIVER-INDEX-1","policy":"Metadata and paths only; never execute or auto-install remote source.","id_databases":ids,"source_indexes":sources}
 output=args.output or (ROOT/"build/driver-source-index.json");output=output if output.is_absolute() else ROOT/output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print("wrote index report: "+str(output));return 0
if __name__=="__main__": raise SystemExit(main())
