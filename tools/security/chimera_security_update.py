#!/usr/bin/env python3
"""Security-intelligence updater with signature/hash verification and atomic activation."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.request
from pathlib import Path

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_sha256(path, expected): return digest(path).lower()==expected.lower()

def update(url, sha256_expected, dest):
    dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False,dir=dest.parent) as tf:
        tmp=Path(tf.name)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-SecurityUpdater/1.0"})
        with urllib.request.urlopen(req,timeout=60) as r, tmp.open("wb") as f:
            while True:
                b=r.read(1024*1024)
                if not b: break
                f.write(b)
        if not verify_sha256(tmp,sha256_expected): raise RuntimeError("security intelligence SHA-256 mismatch")
        data=json.loads(tmp.read_text())
        if data.get("schema")!="CHM-SEC-INTEL-1": raise RuntimeError("unsupported intelligence schema")
        tmp.replace(dest)
        return {"updated":True,"sha256":digest(dest),"version":data.get("version")}
    finally:
        if tmp.exists():
            try: tmp.unlink()
            except OSError: pass

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--url",required=True); ap.add_argument("--sha256",required=True); ap.add_argument("--dest",default="/var/lib/chimera/security/intelligence.json")
    print(json.dumps(update(**vars(ap)),indent=2))
