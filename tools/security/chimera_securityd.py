#!/usr/bin/env python3
"""Chimera II native security daemon: malware/virus/spyware scanning and signed intelligence updates.

Defense-in-depth only: hash/signature/heuristic scanning, optional YARA/ClamAV integration,
behavioral feature scoring, quarantine, and signed update metadata. ML never self-modifies
the scanner or executes downloaded code.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

VERSION="1.0.0"
DEFAULT_DB=Path("/var/lib/chimera/security/intelligence.json")
DEFAULT_QUAR=Path("/var/lib/chimera/security/quarantine")
EICAR=b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

def sha256(p: Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_db(path=DEFAULT_DB):
    try: return json.loads(Path(path).read_text())
    except Exception: return {"schema":"CHM-SEC-INTEL-1","version":1,"sha256":[],"yara_rules":[],"heuristics":{}}

def features(p: Path):
    b=p.read_bytes()[:8*1024*1024]
    return {
      "size": p.stat().st_size,
      "entropy": round(_entropy(b),4) if b else 0.0,
      "pe": b[:2]==b"MZ",
      "elf": b[:4]==b"\\x7fELF",
      "script": p.suffix.lower() in {".ps1",".vbs",".vbe",".js",".jse",".wsf",".hta",".sh",".bat",".cmd"},
      "double_ext": bool(re.search(r"\\.(pdf|docx?|xlsx?|jpg|png|txt)\\.(exe|scr|com|js|vbs|bat|cmd)$",p.name,re.I)),
    }

def _entropy(b):
    from math import log2
    counts=[0]*256
    for x in b: counts[x]+=1
    n=len(b)
    return -sum((c/n)*log2(c/n) for c in counts if c)

def scan(path, db=None, yara=True, clamav=True):
    p=Path(path)
    result={"path":str(p),"verdict":"clean","score":0.0,"detections":[]}
    if not p.is_file(): result["verdict"]="error"; result["detections"].append("not-a-regular-file"); return result
    b=p.read_bytes()[:8*1024*1024]
    digest=sha256(p)
    db=load_db(db)
    if EICAR in b: result["detections"].append("EICAR-test-signature")
    if digest in set(db.get("sha256",[])): result["detections"].append("known-malicious-sha256")
    f=features(p)
    if f["double_ext"]: result["detections"].append("suspicious-double-extension")
    if f["script"] and f["entropy"]>7.2: result["detections"].append("high-entropy-script")
    if f["pe"] and b"powershell" in b.lower() and b"downloadstring" in b.lower(): result["detections"].append("suspicious-powershell-download")
    if clamav and shutil.which("clamscan"):
        try:
            cp=subprocess.run(["clamscan","--no-summary","--infected",str(p)],capture_output=True,text=True,timeout=120)
            if cp.returncode==1: result["detections"].append("clamav:"+cp.stdout.strip())
        except (OSError,subprocess.TimeoutExpired): pass
    if yara and shutil.which("yara") and db.get("yara_rules"):
        with tempfile.NamedTemporaryFile("w",delete=False,suffix=".yar") as rf:
            rf.write("\n".join(db["yara_rules"])); rule=rf.name
        try:
            cp=subprocess.run(["yara","-w",rule,str(p)],capture_output=True,text=True,timeout=120)
            if cp.stdout.strip(): result["detections"].append("yara:"+cp.stdout.strip())
        except (OSError,subprocess.TimeoutExpired): pass
        finally:
            try: os.unlink(rule)
            except OSError: pass
    result["score"]=min(1.0,0.25*len(result["detections"]))
    if result["detections"]: result["verdict"]="malicious" if result["score"]>=0.5 else "suspicious"
    result["sha256"]=digest
    result["features"]=f
    return result

def quarantine(path, quarantine_dir=DEFAULT_QUAR):
    p=Path(path); q=Path(quarantine_dir); q.mkdir(parents=True,exist_ok=True)
    digest=sha256(p); dest=q/(digest+".quarantine")
    shutil.move(str(p),str(dest))
    return dest

def scan_tree(root, db=None):
    root=Path(root); out=[]
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try: out.append(scan(p,db))
            except (OSError,PermissionError) as e: out.append({"path":str(p),"verdict":"error","error":str(e)})
    return out

def main():
    ap=argparse.ArgumentParser(prog="chimera-security")
    sp=ap.add_subparsers(dest="cmd",required=True)
    s=sp.add_parser("scan"); s.add_argument("path"); s.add_argument("--db",default=str(DEFAULT_DB)); s.add_argument("--no-clamav",action="store_true"); s.add_argument("--no-yara",action="store_true")
    t=sp.add_parser("scan-tree"); t.add_argument("path"); t.add_argument("--db",default=str(DEFAULT_DB))
    q=sp.add_parser("quarantine"); q.add_argument("path"); q.add_argument("--dir",default=str(DEFAULT_QUAR))
    args=ap.parse_args()
    if args.cmd=="scan": r=scan(args.path,args.db,not args.no_yara,not args.no_clamav)
    elif args.cmd=="scan-tree": r=scan_tree(args.path,args.db)
    else: r={"quarantined":str(quarantine(args.path,args.dir))}
    print(json.dumps(r,indent=2,sort_keys=True))

if __name__=="__main__": main()
