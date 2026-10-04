#!/usr/bin/env python3
"""Chimera II Mobile ROM/security-resource discovery.

Searches the public web for firmware/ROM resources matching the *exact*
detected device. Only allow-listed official/vendor and project domains are
accepted for automatic download. Security material means public verification
metadata (AVB/vbmeta certificates, hashes, signed metadata and firmware
components); private signing keys, DRM credentials and authentication secrets
are never extracted or downloaded.

The result is a local research bundle. It does not unlock bootloaders,
disable Verified Boot, bypass authentication, or flash anything.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tarfile, tempfile, urllib.parse, zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"build/mobile"
SOURCES=ROOT/"config/mobile-os-sources.json"

DEFAULT_ALLOWLIST={
    "developers.google.com","dl.google.com","android.googleapis.com",
    "source.android.com","lineageos.org","download.lineageos.org",
    "blob.lineageos.org","github.com","gitlab.com","gitlab.postmarketos.org",
    "ubports.com","invent.kde.org","replicant.us","gitee.com",
    "samsung.com","security.samsungmobile.com","motorola.com","lenovo.com",
    "oneplus.com","asus.com","sony.com","fairphone.com","nothing.tech",
    "xiaomi.com","mi.com","huawei.com"
}
SECURITY_NAMES=re.compile(r"(vbmeta(?:_[^/]+)?\.(?:img|bin)|.*avb.*\.(?:pem|pub|pubkey|bin)|.*(?:signature|signed|checksum|sha256|metadata).*|.*rollback.*)",re.I)

def run(cmd, timeout=30):
    return subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b): h.update(b)
    return h.hexdigest()

def host_allowed(url):
    try: host=urllib.parse.urlparse(url).hostname.lower().rstrip(".")
    except Exception: return False
    return any(host==d or host.endswith("."+d) for d in DEFAULT_ALLOWLIST)

def device_queries(target):
    p=target["properties"]
    vals=[p.get("manufacturer",""),p.get("model",""),p.get("device",""),p.get("product",""),p.get("board",""),p.get("platform","")]
    vals=[re.sub(r"[^A-Za-z0-9._ -]","",v).strip() for v in vals if v]
    exact=" ".join(dict.fromkeys(vals))
    return [
        f'"{exact}" firmware ROM download official',
        f'"{p.get("device","")}" "{p.get("model","")}" firmware factory image',
        f'"{p.get("device","")}" site:lineageos.org download',
        f'"{p.get("device","")}" site:developers.google.com/android firmware',
        f'"{p.get("model","")}" site:{p.get("manufacturer","").lower()}.com firmware'
    ]

def web_search(query):
    # DuckDuckGo HTML is used only as a discovery index; downloads are separately allow-listed.
    q=urllib.parse.quote_plus(query)
    url="https://html.duckduckgo.com/html/?q="+q
    r=run(["curl","-fsSL","--retry","3","--max-time","20",url],timeout=30)
    if r.returncode: return []
    links=re.findall(r'nofollow" class="result__a" href="([^"]+)"',r.stdout)
    out=[]
    for x in links[:20]:
        x=x.replace("&amp;","&")
        if x.startswith("//"): x="https:"+x
        if host_allowed(x): out.append(x)
    return list(dict.fromkeys(out))

def official_static_sources(target):
    p=target["properties"]; dev=p.get("device","")
    return [
        {"provider":"Google Android factory images","url":"https://developers.google.com/android/images","type":"factory-images"},
        {"provider":"Google Android full OTA images","url":"https://developers.google.com/android/ota","type":"full-ota"},
        {"provider":"LineageOS device index","url":"https://lineageos.org/download/","type":"custom-rom"},
        {"provider":"LineageOS wiki","url":"https://wiki.lineageos.org/devices/","type":"device-support"},
        {"provider":p.get("manufacturer","OEM")+" official software support","url":"https://"+p.get("manufacturer","").lower()+".com","type":"oem-portal"} if p.get("manufacturer") else {}
    ]

def extract_security(archive:Path, dest:Path):
    dest.mkdir(parents=True,exist_ok=True); found=[]
    def take(name, data):
        base=Path(name).name
        if not base or len(data)>256*1024*1024: return
        if SECURITY_NAMES.search(base):
            out=dest/base
            # Avoid path traversal and overwrite ambiguity.
            if out.exists():
                out=dest/(sha256_bytes(data)[:12]+"-"+base)
            out.write_bytes(data); found.append({"name":base,"path":str(out),"sha256":sha256(out)})
    def sha256_bytes(data):
        return hashlib.sha256(data).hexdigest()
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as z:
                for n in z.namelist():
                    if n.endswith("/") or not SECURITY_NAMES.search(Path(n).name): continue
                    with z.open(n) as f: take(n,f.read(256*1024*1024+1))
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive) as t:
                for m in t.getmembers():
                    if m.isfile() and SECURITY_NAMES.search(Path(m.name).name):
                        f=t.extractfile(m)
                        if f: take(m.name,f.read(256*1024*1024+1))
    except Exception as e:
        found.append({"error":str(e)})
    return found

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target",required=True,help="last-build target JSON or a device target JSON")
    ap.add_argument("--download",action="store_true",help="download only verified allow-listed candidate archives")
    ap.add_argument("--max-downloads",type=int,default=3)
    args=ap.parse_args()
    target=json.loads(Path(args.target).read_text(encoding="utf-8"))
    p=target["properties"]; codename=p.get("device") or p.get("product") or p.get("model")
    root=OUT/"rom-discovery"/re.sub(r"[^A-Za-z0-9_.-]+","_",codename); root.mkdir(parents=True,exist_ok=True)
    queries=device_queries(target)
    candidates=[]
    for q in queries:
        for url in web_search(q):
            candidates.append({"query":q,"url":url,"host":urllib.parse.urlparse(url).hostname})
    candidates= list({x["url"]:x for x in candidates}.values())
    catalog={"schema":"CHM-MOBILE-ROM-CATALOG-1","generated_utc":datetime.now(timezone.utc).isoformat(),"target":target,
             "official_reference_sources":[x for x in official_static_sources(target) if x],
             "search_results":candidates,"policy":{"exact_device_only":True,"official_allowlist_only":True,
             "public_security_metadata_only":True,"no_private_keys":True,"no_auth_bypass":True,
             "no_bootloader_unlock":True,"no_verified_boot_bypass":True}}
    if args.download:
        dl=root/"downloads"; sec=root/"security"; dl.mkdir(exist_ok=True); sec.mkdir(exist_ok=True)
        count=0
        for item in candidates:
            if count>=args.max_downloads: break
            url=item["url"]
            # Search results are pages, not trusted archives; only direct archive URLs are downloaded.
            if not host_allowed(url) or not re.search(r'\.(zip|tgz|tar|gz|img)(?:[?#].*)?$',url,re.I): continue
            fn=Path(urllib.parse.urlparse(url).path).name or f"download-{count}"
            dest=dl/fn
            r=run(["curl","-fL","--retry","3","--max-time","180","-o",str(dest),url],timeout=210)
            if r.returncode: item["download_error"]=r.stdout; continue
            item["downloaded"]=str(dest); item["sha256"]=sha256(dest); item["security_files"]=extract_security(dest,sec); count+=1
    (root/"rom-catalog.json").write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"catalog":str(root/"rom-catalog.json"),"candidates":len(candidates),"downloads":sum(1 for x in candidates if x.get("downloaded")),"security_files":sum(len(x.get("security_files",[])) for x in candidates)},indent=2,ensure_ascii=False))
if __name__=="__main__": main()
