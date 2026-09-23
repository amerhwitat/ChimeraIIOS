#!/usr/bin/env python3
import argparse,json,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("report");p.add_argument("--csv",required=True);a=p.parse_args()
d=json.loads(Path(a.report).read_text(encoding="utf-8"))
with open(a.csv,"w",newline="",encoding="utf-8") as f:
 w=csv.writer(f);w.writerow(["cve","description","references"])
 for x in d.get("cves",[]):
  c=x.get("cve",{});w.writerow([c.get("id",""),c.get("descriptions",[{}])[0].get("value",""),";".join(r.get("url","") for r in c.get("references",[]))])
print(a.csv)