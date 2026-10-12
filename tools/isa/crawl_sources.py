#!/usr/bin/env python3
"""Refresh Chimera's ISA source index and ingest machine-readable instruction records.

This crawler deliberately separates source discovery from instruction implementation.
It downloads only configured public source indexes/files, records hashes and license
metadata, and imports rows only from explicitly supported JSON inputs. It never
scrapes prose into fabricated opcodes or marks an instruction executable merely
because a source mentions it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "isa" / "sources" / "isa-source-manifest.json"
CACHE = ROOT / "isa" / "sources" / "cache"
INDEX = ROOT / "isa" / "generated" / "source-discovery-index.json"
UNIVERSAL = ROOT / "isa" / "generated" / "universal-instruction-catalog.json"

# URLs are source discovery entry points, not blanket licenses to copy vendor text.
# The manifest tracks revision/license before any bulk ingestion.
DEFAULT_SOURCES = [
    {"id":"riscv-unified-db","family":"RISC-V","kind":"machine-readable-database","url":"https://github.com/riscv/riscv-unified-db","license":"check-upstream-file-license","adapter":"json"},
    {"id":"riscv-isa-manual","family":"RISC-V","kind":"official-specification","url":"https://docs.riscv.org/reference/isa/","license":"CC-BY-4.0 for manual source repo; verify each artifact","adapter":"reference-only"},
    {"id":"llvm-mc","family":"multi-architecture","kind":"instruction-descriptions","url":"https://github.com/llvm/llvm-project/tree/main/llvm/lib/Target","license":"Apache-2.0 WITH LLVM-exception; verify files","adapter":"tablegen-index"},
    {"id":"gnu-binutils-opcodes","family":"multi-architecture","kind":"opcode-tables","url":"https://github.com/bminor/binutils-gdb/tree/master/opcodes","license":"GPL and file-specific exceptions; review before ingestion","adapter":"opcode-index"},
    {"id":"qemu-tcg","family":"multi-architecture","kind":"decoder-and-translator","url":"https://github.com/qemu/qemu/tree/master/target","license":"GPL-2.0-or-later; review before ingestion","adapter":"decoder-index"},
    {"id":"intel-sdm","family":"x86-64,x86-32","kind":"official-specification","url":"https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html","license":"Intel terms; reference/link, do not bulk-copy without permission","adapter":"reference-only"},
    {"id":"amd-architecture-programming","family":"x86-64,x86-32","kind":"official-specification","url":"https://www.amd.com/en/search/documentation/hub.html","license":"AMD terms; reference/link, do not bulk-copy without permission","adapter":"reference-only"},
    {"id":"arm-architecture-reference","family":"AArch64,ARM32","kind":"official-specification","url":"https://developer.arm.com/documentation/","license":"Arm terms; reference/link, do not bulk-copy without permission","adapter":"reference-only"},
    {"id":"power-isa","family":"PowerPC","kind":"official-specification","url":"https://openpower.foundation/specifications/","license":"Check individual OpenPOWER specification license","adapter":"reference-only"},
    {"id":"mips-architecture","family":"MIPS32,MIPS64","kind":"specification-index","url":"https://www.mips.com/","license":"Check individual source terms","adapter":"reference-only"},
    {"id":"sparc-architecture","family":"SPARC","kind":"specification-index","url":"https://www.oracle.com/servers/technologies/sparc-architecture.html","license":"Check individual source terms","adapter":"reference-only"},
    {"id":"loongarch-reference","family":"LoongArch","kind":"official-specification","url":"https://loongson.github.io/LoongArch-Documentation/","license":"Check repository/file license","adapter":"reference-only"},
    {"id":"openisa-riscv","family":"RISC-V","kind":"implementation-ecosystem","url":"https://github.com/riscv","license":"Per-repository license","adapter":"repository-index"},
]

def fetch(url: str, timeout: int) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent":"ChimeraIIOS-ISA-Research/1.0","Accept":"text/html,application/json,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), response.geturl()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="fetch configured source entry points")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--cache-dir", type=Path, default=CACHE)
    ap.add_argument("--index", type=Path, default=INDEX)
    ap.add_argument("--strict", action="store_true", help="fail if any configured source cannot be fetched")
    args = ap.parse_args()
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    if args.manifest.exists():
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    else:
        manifest = {"schema":"CHM-ISA-SOURCE-MANIFEST-1","updated_utc":None,"sources":DEFAULT_SOURCES}
        args.manifest.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    records=[]
    failures=[]
    for src in manifest.get("sources", []):
        row={**src,"status":"indexed-only","fetched_url":None,"sha256":None,"bytes":None,"fetched_utc":None,"cache_file":None}
        if args.refresh:
            try:
                body, final_url=fetch(src["url"],args.timeout)
                digest=hashlib.sha256(body).hexdigest()
                args.cache_dir.mkdir(parents=True,exist_ok=True)
                safe=re.sub(r"[^A-Za-z0-9_.-]+","_",src["id"])
                path=args.cache_dir/(safe+"-"+digest[:12]+".source")
                path.write_bytes(body)
                row.update(status="fetched",fetched_url=final_url,sha256=digest,bytes=len(body),
                           fetched_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),cache_file=str(path.relative_to(ROOT)))
            except (OSError, urllib.error.URLError, TimeoutError, KeyError) as exc:
                row["status"]="fetch-failed"; row["error"]=str(exc); failures.append(src.get("id","unknown"))
        records.append(row)
    report={"schema":"CHM-ISA-SOURCE-DISCOVERY-1","generated_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
      "source_count":len(records),"fetched_count":sum(x["status"]=="fetched" for x in records),
      "failed_sources":failures,"sources":records,
      "policy":"Discovery is not ingestion. Vendor prose is not parsed as opcodes. Each imported row must preserve source revision, license, encoding mask, architectural state effects, and execution status."}
    args.index.parent.mkdir(parents=True,exist_ok=True)
    args.index.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"ISA source discovery: {report['fetched_count']}/{len(records)} entry points fetched; index={args.index}")
    if failures:
        print("Unavailable sources: "+", ".join(failures),file=sys.stderr)
        if args.strict: return 2
    print("Note: source discovery does not imply instruction rows were imported or implemented.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
