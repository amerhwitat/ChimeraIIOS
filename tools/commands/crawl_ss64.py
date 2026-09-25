#!/usr/bin/env python3
"""Generate the Chimera II OS SS64 command catalog.

The generator crawls SS64's public index pages and extracts command names from
their A-Z index tables. It intentionally stores names/URLs/namespace metadata,
not SS64 prose. It is network-dependent and should be run by a maintainer or
CI job, not by the boot path.

Usage:
  python3 tools/commands/crawl_ss64.py
  python3 tools/commands/crawl_ss64.py --output system/commands/chimera-command-list.json
"""
import argparse, html.parser, json, re, urllib.parse, urllib.request
from pathlib import Path

INDEXES = {
    "linux_bash": "https://ss64.com/bash/",
    "macos": "https://ss64.com/mac/",
    "windows_cmd": "https://ss64.com/nt/",
    "powershell": "https://ss64.com/ps/",
    "vbscript": "https://ss64.com/vb/",
    "sql_server": "https://ss64.com/sql/",
}

class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.text=[]
        self.in_a=False
        self.href=""
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            self.in_a=True
            self.href=dict(attrs).get("href","")
            self.text=[]
    def handle_data(self, data):
        if self.in_a: self.text.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=="a" and self.in_a:
            label=" ".join("".join(self.text).split())
            if label: self.links.append((label,self.href))
            self.in_a=False
            self.href=""

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-SS64-Catalog/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8","replace")

def clean(label):
    label=re.sub(r"\s+"," ",label).strip()
    label=re.sub(r"\s*[•▫]+\s*$","",label).strip()
    return label

def crawl(index_url):
    p=Parser()
    p.feed(fetch(index_url))
    commands=[]
    seen=set()
    for label,href in p.links:
        label=clean(label)
        if not label or len(label)>100 or label.startswith(("http://","https://")):
            continue
        # SS64 index entries normally point at command/detail pages.
        absolute=urllib.parse.urljoin(index_url,href)
        if absolute not in seen:
            seen.add(absolute)
            commands.append({"name":label,"url":absolute})
    return commands

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="system/commands/chimera-command-list.json")
    args=ap.parse_args()
    catalog={"schema_version":"generated","product":"Chimera II OS",
             "sources":list(INDEXES.values()),"platforms":{}}
    for platform,url in INDEXES.items():
        catalog["platforms"][platform]={"index":url,"commands":crawl(url)}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Wrote {args.output}")
    print("Platform counts:")
    for k,v in catalog["platforms"].items():
        print(f"  {k}: {len(v['commands'])}")

if __name__=="__main__":
    main()
