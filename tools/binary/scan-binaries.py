#!/usr/bin/env python3
"""Recursively inspect executable headers without executing discovered files."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
INSPECTOR=ROOT/"tools/inspect-binary-headers.py"
spec=importlib.util.spec_from_file_location("chm_binary_inspector",INSPECTOR)
if spec is None or spec.loader is None: raise SystemExit("binary header inspector unavailable")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
SKIP={".git",".cache","node_modules","__pycache__",".venv","venv"}
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("root",type=Path,nargs="?",default=Path("."))
 p.add_argument("--json",type=Path,default=Path("binary-scan-report.json")); p.add_argument("--max-size",type=int,default=512*1024*1024); p.add_argument("--include-vendor",action="store_true")
 a=p.parse_args(); root=a.root.resolve(); rows=[]
 for path in root.rglob("*"):
  if not path.is_file(): continue
  rel=path.relative_to(root)
  if any(part in SKIP for part in rel.parts) or (not a.include_vendor and "vendor" in rel.parts): continue
  try:
   size=path.stat().st_size
   if size==0 or size>a.max_size: continue
   with path.open("rb") as f: data=f.read(4096)
   result=module.inspect(data)
   if result["format"]=="unknown": continue
   digest=hashlib.sha256()
   with path.open("rb") as f:
    for chunk in iter(lambda:f.read(1024*1024),b""): digest.update(chunk)
   rows.append({"path":str(rel),"size":size,"sha256":digest.hexdigest(),**result})
  except (OSError,ValueError) as exc: rows.append({"path":str(rel),"error":str(exc)})
 report={"schema":"chm-binary-scan-v1","root":str(root),"files_scanned":len(rows),"executables":rows}
 a.json.parent.mkdir(parents=True,exist_ok=True); a.json.write_text(json.dumps(report,indent=2)+"\n")
 print(f"inspected {len(rows)} executable/container files; report: {a.json}")
 return 0
if __name__=="__main__": raise SystemExit(main())
