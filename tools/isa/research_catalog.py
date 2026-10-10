#!/usr/bin/env python3
"""Bounded recursive ISA web research; discovery never implies executable support."""
import argparse, datetime as dt, hashlib, html.parser, json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs"/"research"
DB_PATH=ROOT/"isa"/"isa_database.json"
SOURCE_PATH=ROOT/"data"/"isa"/"online-source-catalog.json"
UA="ChimeraIIOS-ISA-Research/2.0 (+https://github.com/amerhwitat/ChimeraIIOS)"
MAX_BYTES=1_500_000
TIMEOUT=9
MAX_PAGES=int(os.environ.get("CHIMERA_ISA_RESEARCH_MAX_PAGES","80"))
MAX_DEPTH=int(os.environ.get("CHIMERA_ISA_RESEARCH_MAX_DEPTH","2"))
RELEVANT=re.compile(r"(isa|instruction|architecture|manual|reference|specification|extension|opcode|mnemonic|encoding|decoder|programmer.?s.?guide|processor)",re.I)
SKIP=re.compile(r"(login|logout|privacy|cookie|terms|contact|careers|press|events|shopping|cart|download\?.*utm)",re.I)

CPU_FAMILIES=[
 {"id":"x86","name":"x86 / x86-64 (Intel and AMD)","style":"CISC","sources":["https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html","https://www.amd.com/en/search/documentation/hub.html"],"query":"x86 x86-64 instruction set architecture reference manual opcode decoder"},
 {"id":"arm","name":"Arm / AArch32 / AArch64","style":"RISC","sources":["https://developer.arm.com/documentation","https://developer.arm.com/Architectures"],"query":"Arm AArch64 ARMv8 ARMv9 instruction set architecture reference manual"},
 {"id":"riscv","name":"RISC-V (RV32/RV64 and extensions)","style":"RISC","sources":["https://docs.riscv.org/reference/isa/","https://riscv.org/specifications/ratified/"],"query":"RISC-V ISA specification instruction decoder extension"},
 {"id":"mips","name":"MIPS32 / MIPS64","style":"RISC","sources":["https://www.mips.com/technical-documents/"],"query":"MIPS32 MIPS64 instruction set architecture manual opcode reference"},
 {"id":"power","name":"Power ISA / PowerPC","style":"RISC","sources":["https://openpower.foundation/specifications/isa/"],"query":"OpenPOWER Power ISA instruction set architecture specification"},
 {"id":"sparc","name":"SPARC / SPARC V9","style":"RISC","sources":["https://docs.oracle.com/cd/E18752_01/html/816-1681/sparcv9-30990.html"],"query":"SPARC V9 architecture manual instruction set reference"},
 {"id":"loongarch","name":"LoongArch","style":"RISC","sources":["https://loongson.github.io/LoongArch-Documentation/LoongArch-Vol1-EN.html"],"query":"LoongArch instruction set reference manual architecture"},
 {"id":"xtensa","name":"Xtensa","style":"configurable RISC","sources":["https://www.cadence.com/en_US/home/tools/silicon-solutions/compute-ip/xtensa.html","https://github.com/espressif/xtensa-isa-doc"],"query":"Xtensa ISA instruction set reference manual decoder"},
 {"id":"avr","name":"AVR (8-bit AVR / AVR32 family)","style":"RISC microcontroller","sources":["https://onlinedocs.microchip.com/"],"query":"Microchip AVR instruction set manual AVR opcodes"},
 {"id":"superh","name":"SuperH / SH-2 / SH-4","style":"RISC","sources":["https://www.renesas.com/en/document"],"query":"SuperH SH-4 instruction set architecture programming manual"},
 {"id":"openrisc","name":"OpenRISC / OR1K","style":"RISC","sources":["https://openrisc.io/"],"query":"OpenRISC 1000 architecture manual instruction set OR1K"},
]
GENERAL_QUERIES=["instruction set architecture assembler disassembler","CPU instruction encoding conformance test suite","operating system kernel scheduler drivers","uefi acpi firmware tables syscall compatibility layer"]

class Links(html.parser.HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True); self.href=None; self.parts=[]; self.items=[]
 def handle_starttag(self,tag,attrs):
  if tag.lower()=="a":
   self.href=dict(attrs).get("href"); self.parts=[]
 def handle_data(self,data):
  if self.href is not None: self.parts.append(data)
 def handle_endtag(self,tag):
  if tag.lower()=="a" and self.href is not None:
   label=" ".join(" ".join(self.parts).split())
   if label: self.items.append((label,self.href))
   self.href=None; self.parts=[]

def fetch(url,headers=None):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,text/plain,application/json,application/vnd.github+json,*/*",**(headers or {})})
 try:
  with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
   raw=r.read(MAX_BYTES+1)
   if len(raw)>MAX_BYTES: raw=raw[:MAX_BYTES]
   return r.status,raw.decode(r.headers.get_content_charset() or "utf-8","replace"),r.geturl(),r.headers.get_content_type()
 except Exception as e: return 0,str(e),url,""

def canon(base,href):
 u=urllib.parse.urljoin(base,href); p=urllib.parse.urlparse(u)
 if p.scheme not in ("http","https") or not p.netloc or p.path.lower().endswith((".pdf",".zip",".gz",".png",".jpg",".svg",".mp4",".exe",".dmg")): return ""
 return urllib.parse.urlunparse((p.scheme,p.netloc,p.path,"","",""))

def crawl(seed,depth,visited,records,budget):
 queue=[(seed,0)]
 host=urllib.parse.urlparse(seed).netloc.lower()
 while queue and budget[0]>0:
  url,level=queue.pop(0)
  if url in visited or level>depth or SKIP.search(url): continue
  visited.add(url); budget[0]-=1
  status,body,final,ctype=fetch(url)
  rec={"url":final,"http_status":status,"depth":level,"checked_at":dt.datetime.now(dt.timezone.utc).isoformat(),"content_type":ctype}
  if status:
   rec["sha256"]=hashlib.sha256(body.encode()).hexdigest(); rec["bytes_read"]=len(body.encode())
   rec["title_or_text"]=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",body)).strip()[:320]
  else: rec["error"]=body[:240]
  records.append(rec)
  if status and level<depth and ("html" in ctype or "<html" in body[:500].lower()):
   parser=Links()
   try: parser.feed(body)
   except Exception: pass
   candidates=[]
   for label,href in parser.items:
    u=canon(final,href)
    if not u or urllib.parse.urlparse(u).netloc.lower()!=host or u in visited: continue
    if RELEVANT.search(label+" "+u): candidates.append(u)
   for u in sorted(set(candidates))[:8]: queue.append((u,level+1))
  time.sleep(0.03)

def local_files():
 out=[]
 roots=[ROOT/"isa",ROOT/"tools"/"isa",ROOT/"config",ROOT/"docs",ROOT/"system",ROOT/"data"/"isa",ROOT/"kernel"/"generated"]
 exts={".json",".md",".rst",".txt",".yaml",".yml",".h"}
 for base in roots:
  if not base.exists(): continue
  for p in base.rglob("*"):
   if not p.is_file() or p.suffix.lower() not in exts or any(x in {".git","node_modules","build","dist","__pycache__"} for x in p.parts): continue
   try:
    b=p.read_bytes()
    if len(b)>2_000_000: continue
    if re.search(r"\b(isa|instruction|opcode|mnemonic|syscall|kernel|driver|firmware|command|scheduler|interrupt|android|arm64|risc.?v|x86|loongarch|xtensa|sparc|mips|powerpc|superh|openrisc|avr)\b",p.name+" "+b[:15000].decode("utf-8","replace"),re.I):
     out.append({"path":p.relative_to(ROOT).as_posix(),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
   except OSError: pass
 lib=Path(os.environ.get("CHIMERA_RESEARCH_LIBRARY_DIR",str(OUT/"library-import"))).expanduser()
 if lib.exists():
  for p in lib.rglob("*"):
   if p.is_file() and p.suffix.lower() in exts:
    try:
     b=p.read_bytes()
     if len(b)<=2_000_000: out.append({"path":str(p),"kind":"library-export","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
    except OSError: pass
 return out

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--offline",action="store_true",help="index local catalogs only; do not access the internet")
 ap.add_argument("--refresh",action="store_true",help="perform bounded recursive research and append unverified candidates to the ISA database")
 args=ap.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 local=local_files(); db=json.loads(DB_PATH.read_text(encoding="utf-8")); source_doc=json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
 docs=[]; searches=[]; repositories={}; recursive=[]; candidates=[]; family_results=[]
 if not args.offline:
  seeds=[]
  for f in CPU_FAMILIES:
   seeds.extend((u,f["id"]) for u in f["sources"])
  for s in source_doc.get("isa_sources",[]):
   if s.get("kind","").startswith(("official","architecture","instruction","official-specification")) or "tablegen" in s.get("id",""):
    seeds.append((s["url"],s["id"]))
  visited=set(); budget=[MAX_PAGES]
  for seed,family_id in seeds:
   if budget[0]<=0: break
   start=len(recursive)
   crawl(seed,MAX_DEPTH,visited,recursive,budget)
   for rec in recursive[start:]: rec["family_or_source_id"]=family_id
  # Directly inspect machine-readable LLVM TableGen references for candidate IDs.
  arch_support={s["id"]:s.get("supports",[]) for s in source_doc.get("isa_sources",[])}
  for source in source_doc.get("isa_sources",[]):
   if "tablegen" not in source.get("id",""): continue
   status,body,url,ctype=fetch(source["url"])
   row={"source_id":source["id"],"url":url,"status":status,"authority":source.get("authority"),"family":source.get("family"),"checked_at":dt.datetime.now(dt.timezone.utc).isoformat()}
   if status:
    names=sorted(set(re.findall(r"(?m)^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\b",body)))
    row.update({"candidate_count":len(names),"sha256":hashlib.sha256(body.encode()).hexdigest()})
    for name in names[:500]:
     candidates.append({"source_id":source["id"],"source_url":url,"family":source.get("family"),"architecture_candidates":arch_support.get(source["id"],[]),"candidate_id":name,"status":"unverified-definition-candidate","encoding_verified":False,"executable_support":False})
   else: row["error"]=body[:200]
   docs.append(row)
  headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
  if os.environ.get("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
  for family_id,q in [(f["id"],f["query"]) for f in CPU_FAMILIES]+[("general",q) for q in GENERAL_QUERIES]:
   url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":q,"sort":"updated","order":"desc","per_page":8})
   status,body,final,ctype=fetch(url,headers); row={"family_id":family_id,"query":q,"status":status,"url":final,"repositories":[]}
   if status==200:
    try:
     for r in json.loads(body).get("items",[]):
      name=r.get("full_name")
      if name: repositories.setdefault(name.lower(),{"name":name,"url":r.get("html_url"),"description":(r.get("description") or "")[:400],"language":r.get("language"),"stars":r.get("stargazers_count",0),"updated_at":r.get("updated_at"),"license":(r.get("license") or {}).get("spdx_id"),"query":q,"family_id":family_id,"review_required":True}); row["repositories"].append(name)
    except (ValueError,TypeError): row["error"]="Invalid GitHub JSON"
   else: row["error"]=body[:200]
   searches.append(row); time.sleep(.1)
  if args.refresh and candidates:
   prior=db.get("research_candidates",[])
   keys={(x.get("source_id"),x.get("candidate_id")) for x in prior if isinstance(x,dict)}
   for c in candidates:
    if (c["source_id"],c["candidate_id"]) not in keys: prior.append(c); keys.add((c["source_id"],c["candidate_id"]))
   db["research_candidates"]=prior
   db["research_update"]={**db.get("research_update",{}),"last_recursive_research_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"recursive_pages_visited":len(visited),"recursive_page_budget":MAX_PAGES,"recursive_depth_limit":MAX_DEPTH,"candidate_count_total":len(prior),"policy":"Unverified candidates are metadata only. They are not appended to executable instructions until checked against versioned normative encodings and tests."}
   tmp=DB_PATH.with_suffix(".json.research.tmp"); tmp.write_text(json.dumps(db,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); tmp.replace(DB_PATH)
  for f in CPU_FAMILIES:
   family_results.append({**f,"source_checks":[{"url":r["url"],"http_status":r["http_status"],"depth":r["depth"]} for r in recursive if r.get("family_or_source_id")==f["id"]],"search_status":next((s["status"] for s in searches if s["family_id"]==f["id"]),0),"repository_count":sum(1 for r in repositories.values() if r.get("family_id")==f["id"])})
 else: family_results=CPU_FAMILIES
 report={"schema":"CHIMERA-RESEARCH-CATALOG-3","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"cpu_families":family_results,"policy":{"discovery_only":True,"remote_code_execution":False,"automatic_executable_instruction_import":False,"review_required_before_adoption":True,"official_sources_preferred":True,"recursive_depth":MAX_DEPTH,"page_budget":MAX_PAGES,"note":"Web pages, links, repositories and TableGen def IDs are discovery leads, not proof of ISA conformance or runtime support.","library_export_dir":os.environ.get("CHIMERA_RESEARCH_LIBRARY_DIR",str(OUT/"library-import")),"library_note":"Export selected Library documents into this directory to index them; the build cannot access the Library service directly."},"local_files":local,"recursive_source_checks":recursive,"definition_candidate_sources":docs,"instruction_candidates_added_this_run":len(candidates) if args.refresh else 0,"github_searches":searches,"repositories":sorted(repositories.values(),key=lambda r:r["stars"],reverse=True)}
 (OUT/"isa-command-research.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 lines=["# ISA, command, kernel and mobile OS research","","Generated: "+report["generated_at"],"","> Discovery only: remote code is not executed. Definition identifiers are unverified candidates and are never silently promoted to executable instruction rows.","","## Eleven processor ISA families",""]
 lines += ["- **"+f["name"]+"** ("+f["style"]+"): "+", ".join("["+u+"]("+u+")" for u in f["sources"]) for f in CPU_FAMILIES]
 lines += ["","## Recursive source checks",""]+["- ["+r["url"]+"]("+r["url"]+") — HTTP "+str(r["http_status"])+", depth "+str(r["depth"])+", "+str(r.get("bytes_read",0))+" bytes" for r in recursive]
 lines += ["","## Machine-readable definition candidates","",str(len(candidates))+" unverified identifiers were observed in configured LLVM TableGen sources. These are not assumed to be architectural mnemonics and have no encoding/conformance claim."]
 lines += ["","## GitHub repository discoveries","", "Search results are capped and subject to API limits; review license, provenance, and maintenance before reuse."]
 lines += ["- ["+str(r["name"])+"]("+str(r["url"])+") — "+str(r["description"] or "No description")+"; language "+str(r["language"] or "unknown")+"; stars "+str(r["stars"])+"; license "+str(r["license"] or "unspecified")+"; family "+str(r.get("family_id") or "general") for r in report["repositories"]]
 lines += ["","## Local and Library-exported files",""]+["- "+x["path"]+" — "+str(x["bytes"])+" bytes; SHA-256 "+x["sha256"] for x in local]
 lines += ["","## Adoption and support policy","","1. Verify each candidate against a versioned normative ISA specification and exact architecture/profile/extension.","2. Add encodings only after operand-field, reserved/illegal encoding, assembler/disassembler round-trip, and negative tests pass.","3. Review repository license and security before reusing code.","4. Catalog presence is not compiler, decoder, emulator, hardware, or boot support.","5. Export relevant Library documents into the configured Library directory; direct Library access is unavailable to the build.",""]
 (OUT/"ISA_COMMAND_RESEARCH.md").write_text("\n".join(lines),encoding="utf-8")
 print("[ISA-RESEARCH] local=%d recursively_checked=%d families=%d repositories=%d candidates=%d"%(len(local),len(recursive),len(CPU_FAMILIES),len(repositories),len(candidates)))
 print("[ISA-RESEARCH] wrote docs/research/isa-command-research.json and ISA_COMMAND_RESEARCH.md")
 return 0
if __name__=="__main__": raise SystemExit(main())
