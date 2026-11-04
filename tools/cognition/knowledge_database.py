#!/usr/bin/env python3
"""Validate, search and append source-attributed Chimera AI knowledge records."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "CHIMERA-HARDWARE-SYSTEMS-KNOWLEDGE-1"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,127}$")

def read_db(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("schema")!=SCHEMA:
        raise ValueError("unsupported knowledge database schema")
    if not isinstance(data.get("sources"),list) or not isinstance(data.get("entries"),list):
        raise ValueError("sources and entries must be arrays")
    source_ids={x.get("id") for x in data["sources"] if isinstance(x,dict)}
    seen=set()
    for row in data["entries"]:
        validate_entry(row,source_ids)
        if row["id"] in seen: raise ValueError("duplicate entry id: "+row["id"])
        seen.add(row["id"])
    if data.get("entry_count")!=len(data["entries"]):
        raise ValueError("entry_count does not match entries length")
    return data

def validate_entry(row, source_ids):
    if not isinstance(row,dict): raise ValueError("entry must be an object")
    for key in ("id","domain","title","summary","status","verification"):
        if not isinstance(row.get(key),str) or not row[key].strip():
            raise ValueError("entry requires non-empty string "+key)
    if not ID_RE.fullmatch(row["id"]): raise ValueError("invalid entry id: "+row["id"])
    if not isinstance(row.get("tags"),list) or not all(isinstance(x,str) for x in row["tags"]):
        raise ValueError("tags must be an array of strings")
    refs=row.get("source_ids")
    if not isinstance(refs,list) or not refs or not all(x in source_ids for x in refs):
        raise ValueError("every entry must cite one or more known source_ids")
    if "facts" in row and not isinstance(row["facts"],dict):
        raise ValueError("facts must be an object")

def canonical_hash(row):
    clean={k:v for k,v in row.items() if k not in {"record_hash","appended_utc"}}
    return hashlib.sha256(json.dumps(clean,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def atomic_write(path,data):
    path=Path(path).expanduser()
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)

def validate(args):
    db=read_db(args.database)
    print(json.dumps({"status":"valid","entries":len(db["entries"]),"sources":len(db["sources"]),"version":db["version"]}))
    return 0

def search(args):
    db=read_db(args.database)
    terms=set(re.findall(r"[\w-]{2,}",args.query.casefold()))
    ranked=[]
    for row in db["entries"]:
        hay=(row["title"]+" "+row["summary"]+" "+" ".join(row["tags"])).casefold()
        score=sum(hay.count(t) for t in terms)
        if score:
            source_map={s["id"]:s for s in db["sources"]}
            ranked.append((score,{"id":row["id"],"domain":row["domain"],"title":row["title"],"summary":row["summary"],"score":score,
              "sources":[{"id":sid,"title":source_map[sid]["title"],"url":source_map[sid]["url"]} for sid in row["source_ids"]]}))
    ranked.sort(key=lambda x:(-x[0],x[1]["id"]))
    print(json.dumps([x[1] for x in ranked[:max(1,min(args.limit,50))]],ensure_ascii=False,indent=2))
    return 0

def append(args):
    base=Path(args.database).expanduser()
    if base.exists():
        db=read_db(base)
    elif args.base:
        db=read_db(args.base)
    else:
        raise SystemExit("database does not exist; pass --base to seed the user database")
    raw=json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows=raw if isinstance(raw,list) else [raw]
    source_ids={s["id"] for s in db["sources"]}
    existing={r["id"] for r in db["entries"]}
    added=[]
    for row in rows:
        validate_entry(row,source_ids)
        if row["id"] in existing:
            raise SystemExit("refusing duplicate entry id: "+row["id"])
        item=dict(row)
        item["appended_utc"]=datetime.now(timezone.utc).isoformat()
        item["record_hash"]=canonical_hash(item)
        db["entries"].append(item); existing.add(item["id"]); added.append(item["id"])
    db["entry_count"]=len(db["entries"])
    db["updated_utc"]=datetime.now(timezone.utc).isoformat()
    parts=[int(x) for x in db.get("version","1.0.0").split(".")]
    db["version"]=".".join(map(str,(parts[0],parts[1],parts[2]+1)))
    atomic_write(base,db)
    print(json.dumps({"status":"appended","added":added,"entry_count":db["entry_count"],"version":db["version"]}))
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate");v.add_argument("--database",required=True);v.set_defaults(func=validate)
    s=sub.add_parser("search");s.add_argument("--database",required=True);s.add_argument("--query",required=True);s.add_argument("--limit",type=int,default=10);s.set_defaults(func=search)
    a=sub.add_parser("append");a.add_argument("--database",required=True);a.add_argument("--base");a.add_argument("--input",required=True);a.set_defaults(func=append)
    args=p.parse_args()
    try:return args.func(args)
    except (OSError,ValueError,json.JSONDecodeError) as exc: raise SystemExit(str(exc))
if __name__=="__main__": raise SystemExit(main())
