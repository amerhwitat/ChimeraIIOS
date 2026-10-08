#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,tempfile,urllib.request
from pathlib import Path
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def update(url,sha256_expected,dest):
    dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False,dir=dest.parent) as tf: tmp=Path(tf.name)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-SecurityUpdater/1.0"})
        with urllib.request.urlopen(req,timeout=60) as r,tmp.open("wb") as f:
            while True:
                b=r.read(1024*1024)
                if not b: break
                f.write(b)
        if digest(tmp).lower()!=sha256_expected.lower(): raise RuntimeError("security intelligence SHA-256 mismatch")
        data=json.loads(tmp.read_text())
        if data.get("schema")!="CHM-SEC-INTEL-1": raise RuntimeError("unsupported intelligence schema")
        tmp.replace(dest)
        return {"updated":True,"sha256":digest(dest),"version":data.get("version")}
    finally:
        if tmp.exists():
            try: tmp.unlink()
            except OSError: pass
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--url"); ap.add_argument("--sha256"); ap.add_argument("--dest",default="/var/lib/chimera/security/intelligence.json")
    ap.add_argument("--config",default="/etc/chimera/security-update.json")
    a=ap.parse_args()
    if a.config and Path(a.config).is_file():
        c=json.loads(Path(a.config).read_text())
        a.url=c.get("url") or a.url; a.sha256=c.get("sha256") or a.sha256; a.dest=c.get("dest",a.dest)
    if not a.url or not a.sha256:
        print(json.dumps({"updated":False,"status":"not-configured"})); return 0
    print(json.dumps(update(a.url,a.sha256,a.dest),indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
