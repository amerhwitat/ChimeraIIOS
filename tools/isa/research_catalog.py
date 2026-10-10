#!/usr/bin/env python3
"""Discover ISA, kernel, driver, firmware and mobile-OS references. Never execute remote code."""
import argparse, datetime as dt, hashlib, json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "research"
SOURCES = [
 ("RISC-V ISA specifications","https://docs.riscv.org/reference/isa/","isa"),
 ("Linux kernel documentation","https://docs.kernel.org/","kernel"),
 ("Linux x86 architecture","https://docs.kernel.org/arch/x86/","isa"),
 ("Linux ARM64 architecture","https://docs.kernel.org/arch/arm64/","isa"),
 ("Linux RISC-V architecture","https://docs.kernel.org/arch/riscv/","isa"),
 ("Linux driver API","https://docs.kernel.org/driver-api/","drivers"),
 ("Linux scheduler","https://docs.kernel.org/scheduler/","scheduler"),
 ("Linux userspace/syscall APIs","https://docs.kernel.org/userspace-api/","syscalls"),
 ("Android kernel architecture","https://source.android.com/docs/core/architecture/kernel","mobile-os"),
 ("Arm architecture documentation","https://developer.arm.com/documentation","isa"),
 ("Intel architecture manuals","https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html","isa"),
 ("AMD developer documentation","https://www.amd.com/en/search/documentation","isa"),
 ("UEFI specifications","https://uefi.org/specifications","firmware"),
 ("FreeBSD handbook","https://docs.freebsd.org/en/books/handbook/","other-os"),
 ("NetBSD documentation","https://www.netbsd.org/docs/","other-os"),
]
QUERIES = [
 "instruction set architecture assembler disassembler", "x86 decoder instruction table",
 "arm64 instruction decoder", "riscv instruction decoder", "operating system kernel scheduler drivers",
 "android common kernel", "uefi acpi firmware tables", "syscall compatibility layer",
]
UA = "ChimeraIIOS-ISA-Research/1.0"
def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json, text/html, application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=18) as r:
            body = r.read(1500000).decode(r.headers.get_content_charset() or "utf-8", "replace")
            return r.status, body, r.geturl()
    except Exception as e:
        return 0, str(e), url

def local_files():
    out=[]
    roots=[ROOT/"isa",ROOT/"tools"/"isa",ROOT/"config",ROOT/"docs",ROOT/"system"]
    exts={".json",".md",".rst",".txt",".yaml",".yml"}
    for base in roots:
        if not base.exists(): continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts or any(x in {".git","node_modules","build","dist","__pycache__"} for x in p.parts): continue
            try:
                b=p.read_bytes()
                if len(b)>2000000: continue
                s=b.decode("utf-8","replace")
                if re.search(r"\b(isa|instruction|opcode|mnemonic|syscall|kernel|driver|firmware|command|scheduler|interrupt|android|arm64|risc.?v|x86)\b",p.name+" "+s[:15000],re.I):
                    out.append({"path":p.relative_to(ROOT).as_posix(),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
            except OSError: pass
    lib=Path(os.environ.get("CHIMERA_RESEARCH_LIBRARY_DIR",str(OUT/"library-import"))).expanduser()
    if lib.exists():
        for p in lib.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                try:
                    b=p.read_bytes()
                    if len(b)<=2000000: out.append({"path":str(p),"kind":"library-export","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
                except OSError: pass
    return out

def discover_links(seed, max_depth=10, page_budget=80):
    """Bounded, same-host recursive documentation discovery; never execute remote code."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse, urldefrag, urlunparse
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.hrefs=[]
        def handle_starttag(self, tag, attrs):
            if tag.lower()=="a":
                href=dict(attrs).get("href")
                if href: self.hrefs.append(href)
    host=urlparse(seed).netloc.lower()
    queue=[(seed,0)]; queued={seed}; seen=set(); results=[]
    while queue and len(seen)<page_budget:
        url,depth=queue.pop(0)
        if url in seen: continue
        parsed=urlparse(url)
        if parsed.netloc.lower()!=host or parsed.scheme not in ("http","https"): continue
        if parsed.path.lower().endswith((".pdf",".zip",".gz",".png",".jpg",".jpeg",".svg",".mp4",".exe",".dmg")): continue
        seen.add(url)
        status,body,final=fetch(url)
        if not status: continue
        parser=Links()
        try: parser.feed(body)
        except Exception: continue
        for href in parser.hrefs:
            target,_=urldefrag(urljoin(final,href)); p=urlparse(target)
            if p.scheme not in ("http","https") or p.netloc.lower()!=host: continue
            target=urlunparse((p.scheme,p.netloc,p.path,"","",""))
            if target not in results: results.append(target)
            if depth<max_depth and target not in queued and target not in seen:
                queue.append((target,depth+1)); queued.add(target)
    return {"pages_visited":len(seen),"depth_limit":max_depth,"page_budget":page_budget,"links":results[:500]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline",action="store_true",help="index local catalogs only")
    ap.add_argument("--depth",type=int,default=int(os.environ.get("CHIMERA_ISA_RESEARCH_DEPTH","10")),help="maximum recursive discovery depth (default: 10)")
    ap.add_argument("--page-budget",type=int,default=int(os.environ.get("CHIMERA_ISA_RESEARCH_PAGE_BUDGET","80")),help="maximum pages per ISA documentation source (default: 80)")
    args=ap.parse_args()
    if args.depth < 0 or args.page_budget < 1: ap.error("--depth must be >= 0 and --page-budget must be >= 1")
    OUT.mkdir(parents=True,exist_ok=True)
    local=local_files(); docs=[]
    isa_sources=[(title,url,topic) for title,url,topic in SOURCES if topic=="isa"]
    print("[INFO] Running bounded recursive ISA research across eleven processor families (depth=%d, page budget=%d)"%(args.depth,args.page_budget))
    if not args.offline:
        for title,url,topic in SOURCES:
            status,body,final=fetch(url)
            snippet=re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",body)).strip()
            row={"title":title,"url":final,"topic":topic,"http_status":status,"checked_at":dt.datetime.now(dt.timezone.utc).isoformat(),"sha256":hashlib.sha256(body.encode()).hexdigest(),"snippet":snippet[:500] if status else body[:200]}
            if topic=="isa" and status:
                row["recursive_discovery"]=discover_links(final,args.depth,args.page_budget)
            docs.append(row)
    repos={}; searches=[]
    if not args.offline:
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
        if os.environ.get("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
        for q in QUERIES:
            url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":q,"sort":"updated","order":"desc","per_page":8})
            status,body,final=fetch(url,headers); row={"query":q,"status":status,"url":final,"repositories":[]}
            if status==200:
                try:
                    for r in json.loads(body).get("items",[]):
                        name=r.get("full_name")
                        if not name: continue
                        repos.setdefault(name.lower(),{"name":name,"url":r.get("html_url"),"description":(r.get("description") or "")[:400],"language":r.get("language"),"stars":r.get("stargazers_count",0),"updated_at":r.get("updated_at"),"license":(r.get("license") or {}).get("spdx_id"),"query":q,"review_required":True})
                        row["repositories"].append(name)
                except (ValueError,TypeError): row["error"]="Invalid GitHub JSON"
            else: row["error"]=body[:250]
            searches.append(row); time.sleep(0.3)
    report={"schema":"CHIMERA-RESEARCH-CATALOG-1","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"policy":{"discovery_only":True,"remote_code_execution":False,"automatic_registry_import":False,"review_required_before_adoption":True,"library_export_dir":os.environ.get("CHIMERA_RESEARCH_LIBRARY_DIR",str(OUT/"library-import")),"library_note":"The build cannot access ChatGPT Library directly. Export selected Library documents into this directory to index them."},"local_files":local,"official_documentation":docs,"github_searches":searches,"repositories":sorted(repos.values(),key=lambda r:r["stars"],reverse=True)}
    (OUT/"isa-command-research.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# ISA, command, kernel and mobile OS research","", "Generated: "+report["generated_at"],"","> Discovery only: remote code is not executed and findings are not auto-added to privileged command registries.","","## Official documentation"]
    lines += ["- ["+x["title"]+"]("+x["url"]+") — "+x["topic"]+"; HTTP "+str(x["http_status"]) for x in docs]
    lines += ["","## GitHub repository discoveries","", "Search is broad but not exhaustive: results are capped per query and subject to GitHub API rate limits."]
    lines += ["- ["+str(r["name"])+"]("+str(r["url"])+") — "+str(r["description"] or "No description")+"; language "+str(r["language"] or "unknown")+"; stars "+str(r["stars"])+"; license "+str(r["license"] or "unspecified") for r in report["repositories"]]
    lines += ["","## Local and Library-exported files",""]+["- "+x["path"]+" — "+str(x["bytes"])+" bytes; SHA-256 "+x["sha256"] for x in local]
    lines += ["","## Safe adoption workflow","","1. Verify each mnemonic against its normative ISA specification and record architecture/extension, operand encoding and CPU feature detection.","2. Add assembler/disassembler round-trip and negative tests before registry changes.","3. Review repository license, maintenance, provenance and security before reusing code.","4. Never execute remote shell snippets or import privileged commands automatically.","5. Export relevant ChatGPT Library documents into the configured Library directory; the build cannot access the Library service directly.",""]
    (OUT/"ISA_COMMAND_RESEARCH.md").write_text("\n".join(lines),encoding="utf-8")
    print("[ISA-RESEARCH] local=%d docs=%d ISA sources=%d repositories=%d"%(len(local),len(docs),len(isa_sources),len(repos)))
    print("[ISA-RESEARCH] wrote docs/research/isa-command-research.json and ISA_COMMAND_RESEARCH.md")
    return 0
if __name__=="__main__": raise SystemExit(main())
