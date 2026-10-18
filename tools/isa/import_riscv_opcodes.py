#!/usr/bin/env python3
"""Import source-backed RISC-V instruction encoding masks from riscv-opcodes.

This adapter imports fixed-bit encodings only. It deliberately leaves register
effects and executable semantics unknown unless supplied by a separate semantic
source; an encoding row is not an implementation claim.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "isa" / "sources" / "imports" / "riscv-opcodes.json"
DEFAULT_REVISION = "5783cf3bea312a48d28e3e2c8a2fcb55603e4bed"
API_TREE = "https://api.github.com/repos/riscv/riscv-opcodes/git/trees/{revision}?recursive=1"
RAW_ROOT = "https://raw.githubusercontent.com/riscv/riscv-opcodes/{revision}/"

def get(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"ChimeraIIOS-ISA-Importer/1.0","Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()

def cached_import_is_valid(path: Path, revision: str) -> bool:
    """Accept only a non-empty import whose every record cites the pinned revision."""
    try:
        cached=json.loads(Path(path).read_text(encoding="utf-8"))
        records=cached.get("instructions",[])
        return (cached.get("schema")=="CHM-ISA-SOURCED-IMPORT-1" and bool(records)
                and cached.get("record_count")==len(records)
                and all(row.get("source_revision")==revision for row in records))
    except (OSError,ValueError,TypeError,AttributeError):
        return False

def parse_file(text: str, path: str, source_hash: str, source_revision: str) -> list[dict]:
    # The upstream files declare fixed fields as NAME hi..lo=value; variable
    # fields are omitted from the fixed mask. Ignore macros, comments and aliases.
    rows=[]
    for lineno,line in enumerate(text.splitlines(),1):
        clean=line.split("#",1)[0].strip()
        if not clean or clean.startswith(("$","@")): continue
        parts=clean.split()
        name=parts[0]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]*",name): continue
        value=mask=0
        saw=False
        highest=-1
        valid=True
        for token in parts[1:]:
            m=re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s+(\d+)\.\.(\d+)=(0x[0-9a-fA-F]+|0b[01]+|[0-9]+)",token)
            if not m:
                # Source grammar also uses spaced field fragments; these are
                # handled by a joined-token pass below.
                continue
        joined=" ".join(parts[1:])
        # Parse repeated "field hi..lo=value" segments without assuming field order.
        matches=list(re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s+(\d+)\.\.(\d+)=(0x[0-9a-fA-F]+|0b[01]+|[0-9]+)",joined))
        for m in matches:
            hi,lo=int(m.group(2)),int(m.group(3))
            try: val=int(m.group(4),0)
            except ValueError: valid=False; break
            if hi < lo or hi >= 64 or lo < 0 or val >= (1 << (hi-lo+1)):
                valid=False; break
            width=hi-lo+1; fieldmask=((1<<width)-1)<<lo
            if mask & fieldmask: valid=False; break
            mask |= fieldmask; value |= val<<lo; highest=max(highest,hi); saw=True
        if not valid or not saw or highest < 6: continue
        # Keep only the base 32-bit opcode files here; variable-length and
        # extension-specific instruction length require explicit source metadata.
        length=32 if highest < 32 else ((highest+8)//8)*8
        fullmask=(1<<length)-1
        bits=format(value & fullmask,f"0{length}b")
        maskbits=format(mask & fullmask,f"0{length}b")
        rows.append({
          "architecture":"riscv32/riscv64","mnemonic":name.upper(),"form_id":f"{path}:{lineno}",
          "operands":"source fields from riscv-opcodes; see source file","syntax":"",
          "length_bits":length,"value_bits":bits,"mask_bits":maskbits,
          "opcode_hex":f"0x{value:0{length//4}x}","encoding":"riscv-opcodes fixed-bit mask",
          "endianness":"instruction-little","instruction_byte_order":"instruction-little",
          "operand_endianness":"architecture-defined","register_classes":[],
          "flags_read":[],"flags_written":[],"memory_effects":"unknown",
          "privilege":"source-defined/unknown","extensions":[Path(path).name],
          "feature_requirements":[],"exceptions":[],"semantic_id":None,
          "native_mapping":None,"compatibility_mapping":None,
          "execution_status":"not-implemented",
          "source_ref":f"https://github.com/riscv/riscv-opcodes/blob/{source_revision}/"+path,
          "source_revision":source_revision,
          "source_sha256":source_hash,"license":"BSD-3-Clause-Clear (verify source file)"
        })
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=OUT_DEFAULT)
    ap.add_argument("--timeout",type=int,default=25)
    ap.add_argument("--max-files",type=int,default=500)
    ap.add_argument("--revision",default=DEFAULT_REVISION,help="immutable upstream commit SHA (40 hex characters)")
    ap.add_argument("--allow-cached",action="store_true",help="reuse an existing schema- and revision-validated import if GitHub rate limits the upstream fetch")
    args=ap.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.revision):
        raise SystemExit("--revision must be an immutable 40-character commit SHA")
    revision=args.revision.lower()
    try:
        tree=json.loads(get(API_TREE.format(revision=revision),args.timeout))
    except Exception as e:
        if args.allow_cached and cached_import_is_valid(args.output,revision):
            cached=json.loads(args.output.read_text(encoding="utf-8"))
            print(f"Using {len(cached['instructions'])} cached source-backed ISA records for pinned revision {revision}; upstream fetch unavailable: {e}")
            return 0
        raise SystemExit(f"cannot retrieve riscv-opcodes source tree: {e}")
    paths=[x["path"] for x in tree.get("tree",[]) if x.get("type")=="blob" and x.get("path","").startswith("extensions/") and Path(x["path"]).suffix in {".", ""}]
    # The repository's extension definition files commonly have no suffix.
    paths=sorted(set(paths))[:args.max_files]
    rows=[]; failures=[]
    for path in paths:
        try:
            body=get(RAW_ROOT.format(revision=revision)+path,args.timeout)
            digest=hashlib.sha256(body).hexdigest()
            rows.extend(parse_file(body.decode("utf-8",errors="replace"),path,digest,revision))
        except (OSError,urllib.error.URLError,TimeoutError,UnicodeError) as e:
            failures.append({"path":path,"error":str(e)})
    unique={}
    for row in rows:
        key=(row["mnemonic"],row["length_bits"],row["value_bits"],row["mask_bits"],row["source_ref"])
        unique[key]=row
    result={"schema":"CHM-ISA-SOURCED-IMPORT-1","source_repository":"https://github.com/riscv/riscv-opcodes",
      "source_tree_sha":tree.get("sha"),"record_count":len(unique),"files_considered":len(paths),
      "failed_files":failures,"instructions":sorted(unique.values(),key=lambda r:(r["mnemonic"],r["form_id"])),
      "limitations":["Encoding masks only; register effects and semantics are not inferred.",
        "Source revision is pinned by immutable commit SHA; review the pin before refreshing.",
        "Review source license and architecture/extension scope before merging."]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Imported {len(unique)} sourced RISC-V encoding records from {len(paths)} source files; failed files={len(failures)}")
    if not unique: return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
