#!/usr/bin/env python3
"""Bounded, opt-in knowledge ingestion for Chimera II Nucleus.

It fetches only explicitly allow-listed HTTPS URLs. It stores provenance and
deduplicated text; model training remains a separate explicit pipeline.
"""
import hashlib,json,os,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"knowledge/updater.json").read_text())
if not CFG.get("enabled"): print("knowledge updater disabled"); sys.exit(0)
urls=CFG.get("allowed_urls",[])
domains=set(CFG.get("allowed_domains",[]))
if not urls: print("no allow-listed URLs"); sys.exit(0)
out=ROOT/"build"/"nucleus"/"knowledge.jsonl"; out.parent.mkdir(parents=True,exist_ok=True)
limit=int(CFG.get("max_document_bytes",10485760)); timeout=int(CFG.get("timeout_seconds",30))
seen=set()
if out.exists():
    for line in out.read_text(errors="ignore").splitlines():
        try: seen.add(json.loads(line)["sha256"])
        except Exception: pass
count=0
for url in urls:
    if count>=int(CFG.get("max_documents_per_cycle",32)): break
    if not url.startswith("https://"): continue
    host=url.split("/",3)[2].lower().split(":")[0]
    if domains and not any(host==d or host.endswith("."+d) for d in domains): continue
    req=urllib.request.Request(url,headers={"User-Agent":"ChimeraII-KnowledgeUpdater/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            data=resp.read(limit+1)
            if len(data)>limit: continue
            text=data.decode("utf-8","ignore")
    except Exception as exc:
        print(f"skip {url}: {exc}",file=sys.stderr); continue
    digest=hashlib.sha256(data).hexdigest()
    if digest in seen: continue
    rec={"url":url,"retrieved_at":datetime.now(timezone.utc).isoformat(),"sha256":digest,"text":text}
    with out.open("a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    seen.add(digest); count+=1
print(f"ingested {count} document(s) into {out}")
