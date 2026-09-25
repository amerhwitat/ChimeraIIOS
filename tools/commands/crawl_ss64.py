#!/usr/bin/env python3
"""Deep SS64 command indexer for Chimera II OS.

Indexes command names and source URLs only; it deliberately does not copy SS64
page prose. It follows same-site links from the SS64 command-reference indexes,
including the root-linked Linux, macOS, CMD, PowerShell, VBScript, SQL/Access
and Tools sections. The result is a machine-readable registry consumed by the
Chimera shell and binary-provider installer.

Usage:
  python3 tools/commands/crawl_ss64.py --output system/commands/ss64-command-catalog.json
"""
import argparse, html.parser, json, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT="https://ss64.com/"
INDEXES={
 "linux_bash":"https://ss64.com/bash/",
 "macos":"https://ss64.com/mac/",
 "windows_cmd":"https://ss64.com/nt/",
 "powershell":"https://ss64.com/ps/",
 "vbscript":"https://ss64.com/vb/",
 "sql_server":"https://ss64.com/sql/",
 "access":"https://ss64.com/access/",
 "tools":"https://ss64.com/tools/",
}
MAX_PAGES=3000

class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]; self._a=False; self._href=""; self._text=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            self._a=True; self._href=dict(attrs).get("href",""); self._text=[]
    def handle_data(self,data):
        if self._a: self._text.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._a:
            self.links.append((" ".join("".join(self._text).split()),self._href))
            self._a=False

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-SS64-Crawler/2.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8","replace")

def clean(s):
    s=re.sub(r"\s+"," ",s or "").strip()
    s=re.sub(r"\s*[•▫]+\s*$","",s).strip()
    return s

def classify(label,url,platform):
    name=clean(label)
    if not name or len(name)>160: return None
    if name in {"Home","Search","Contact","About","Donate","Examples","Syntax","Related"}: return None
    if name.startswith(("http://","https://","mailto:")): return None
    if not re.search(r"[A-Za-z0-9_$?&./+-]",name): return None
    return {"name":name,"url":url,"platform":platform}

def crawl(seed,platform):
    queue=[seed]; seen=set(); entries={}; pages=0
    host=urllib.parse.urlparse(ROOT).netloc
    prefix=urllib.parse.urlparse(seed).path.rstrip("/")+"/"
    while queue and pages<MAX_PAGES:
        url=queue.pop(0)
        if url in seen: continue
        u=urllib.parse.urlparse(url)
        if u.netloc!=host or not u.path.startswith(prefix): continue
        seen.add(url); pages+=1
        try: html=fetch(url)
        except Exception: continue
        p=Parser(); p.feed(html)
        for label,href in p.links:
            absolute=urllib.parse.urljoin(url,href).split("#",1)[0]
            au=urllib.parse.urlparse(absolute)
            if au.netloc!=host or not au.path.startswith(prefix): continue
            if absolute not in seen and absolute not in queue:
                queue.append(absolute)
            item=classify(label,absolute,platform)
            if item:
                key=(item["name"].lower(),item["url"])
                entries[key]=item
        time.sleep(0.03)
    return sorted(entries.values(),key=lambda x:(x["name"].lower(),x["url"])),pages

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="system/commands/ss64-command-catalog.json")
    ap.add_argument("--max-pages",type=int,default=MAX_PAGES)
    args=ap.parse_args()
    global MAX_PAGES
    MAX_PAGES=max(1,args.max_pages)
    out={"schema_version":"3.0","product":"Chimera II OS","source":"SS64",
         "policy":"Names, classifications and source URLs only; no SS64 page prose is redistributed.",
         "platforms":{}}
    for platform,url in INDEXES.items():
        entries,pages=crawl(url,platform)
        out["platforms"][platform]={"index":url,"pages_crawled":pages,"commands":entries}
        print(f"{platform}: {len(entries)} command links across {pages} pages")
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Wrote",args.output)

if __name__=="__main__":
    main()
