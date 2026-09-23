#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,re,sys,urllib.request
from pathlib import Path
BASE=Path(os.environ.get("CHIMERA_APACHE_PREFIX","/opt/chimera/apache"))
CACHE=Path(os.environ.get("CHIMERA_APACHE_CACHE","/var/cache/chimera/apache"))
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Chimera-II-OS-Apache-Integrator/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def install(project,version,url,expected=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*",project):raise ValueError("invalid project")
    if any(x in url.lower() for x in ("snapshot","nightly","unapproved")):raise ValueError("non-release artifact")
    p=CACHE/Path(url).name;p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():p.write_bytes(get(url))
    actual=digest(p)
    if expected and actual.lower()!=expected.lower():raise ValueError("SHA-256 mismatch")
    target=BASE/project/version;target.mkdir(parents=True,exist_ok=True)
    (target/"ARTIFACT").write_text(str(p)+"\n")
    (target/"SHA256").write_text(actual+"  "+p.name+"\n")
    (target/"PROVENANCE.json").write_text(json.dumps({"project":project,"version":version,"source_url":url,"sha256":actual},indent=2)+"\n")
    print(target)
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: apache-sync.py PROJECT VERSION OFFICIAL_RELEASE_URL")
    install(*sys.argv[1:4])
