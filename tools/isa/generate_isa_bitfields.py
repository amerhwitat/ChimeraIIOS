#!/usr/bin/env python3
"""Generate complete Chimera II ISA bitfield metadata without changing the 16-byte ABI."""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path

HEADER=["mnemonic","opcode","encoding","operands","privilege","latency","throughput","pipeline_stage","isa_family","notes","source_ref","encoding_template","opcode_bits","imm_size","modrm_like","example_binary"]
FIELD_RE=re.compile(r"\[(\d+)\s*:\s*(\d+)\s+([^\]]+)\]")
NAMES_RE=re.compile(r'constexpr std::string_view names\s*=\s*\n\s*"([^"]+)";')

def empty_row(mnemonic, opcode): return {k:"" for k in HEADER}|{"mnemonic":mnemonic,"opcode":f"0x{opcode:04X}","source_ref":"cpu_opcode_name_table"}
def load_cpp_names(path:Path):
    if not path.exists(): return {}
    m=NAMES_RE.search(path.read_text(encoding="utf-8"))
    if not m: raise RuntimeError(f"cannot locate kNames string in {path}")
    return {i+1:empty_row(name,i+1) for i,name in enumerate(m.group(1).split()) if name}
def load_rows(paths,cpp):
    merged=load_cpp_names(cpp)
    for path in paths:
        with path.open(newline="",encoding="utf-8") as fh:
            for row in csv.DictReader(fh,delimiter=";"):
                if not row.get("opcode") or not row.get("mnemonic"): continue
                op=int(row["opcode"],16); item={k:row.get(k,"") for k in HEADER}
                if op in merged:
                    for key,value in item.items():
                        if value: merged[op][key]=value
                else: merged[op]=item
    return dict(sorted(merged.items()))
def mask_for(start,end): return ((1<<(end-start+1))-1)<<start
def parse_template(template,opcode):
    fields=[]; errors=[]
    for match in FIELD_RE.finditer(template or ""):
        hi,lo=int(match.group(1)),int(match.group(2)); name=match.group(3).strip()
        if hi<lo: errors.append(f"reversed range {hi}:{lo} for {name}"); continue
        width=hi-lo+1; fields.append({"name":name,"start":lo,"end":hi,"width":width,"mask":f"0x{mask_for(lo,hi):X}","shift":lo})
    if template and not fields: errors.append("no parseable bitfields")
    covered=0
    for f in fields:
        m=int(f["mask"],16)
        if covered&m: errors.append(f"overlapping field {f['name']}")
        covered|=m
    opfield=next((f for f in fields if f["name"]=="opcode"),None)
    if opfield and opcode >= (1<<opfield["width"]): errors.append(f"opcode 0x{opcode:X} does not fit {opfield['width']}-bit opcode field")
    if template and "separate" in template.lower(): errors.append("template contains an unspecified separate field")
    return fields,errors
def abi_fields():
    return [{"name":"opcode","start":0,"end":15,"width":16,"mask":"0x000000000000FFFF","shift":0},{"name":"rd","start":16,"end":31,"width":16,"mask":"0x00000000FFFF0000","shift":16},{"name":"rs","start":32,"end":47,"width":16,"mask":"0x0000FFFF00000000","shift":32},{"name":"rt","start":48,"end":63,"width":16,"mask":"0xFFFF000000000000","shift":48},{"name":"immediate","start":64,"end":127,"width":64,"mask":"0xFFFFFFFFFFFFFFFF0000000000000000","shift":64}]
def make_record(row):
    template=row.get("encoding_template",""); opcode=int(row["opcode"],16); parsed,errors=parse_template(template,opcode)
    status="canonical_abi_only" if not parsed else ("template_review_required" if errors else "template")
    return {"mnemonic":row["mnemonic"],"opcode":f"0x{opcode:04X}","opcode_bits":row.get("opcode_bits","") or f"0x{opcode:X}","encoding":row.get("encoding",""),"operands":row.get("operands",""),"privilege":row.get("privilege",""),"isa_family":row.get("isa_family",""),"encoding_template":template or "[127:64 immediate][63:48 rt][47:32 rs][31:16 rd][15:0 opcode] (canonical host ABI)","encoding_status":status,"bitfields":parsed or abi_fields(),"example_binary":row.get("example_binary",""),"validation_errors":errors,"source_ref":row.get("source_ref","")}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cpp",type=Path,default=Path("src/isa/chimera_isa.cpp")); ap.add_argument("--canonical",type=Path,default=Path("tools/isa/chimera_r8192_opcode_index.csv")); ap.add_argument("--expanded",type=Path,default=Path("tools/isa/isa_opcodes_expanded_with_encodings.csv")); ap.add_argument("--extension",type=Path,default=Path("tools/isa/isa_extension_0092_011c.csv")); ap.add_argument("--output",type=Path,default=Path("tools/isa/isa_bitfields.json")); args=ap.parse_args()
    paths=[p for p in (args.canonical,args.expanded,args.extension) if p.exists()]; rows=load_rows(paths,args.cpp); instructions=[make_record(row) for row in rows.values()]
    doc={"schema":"chimera-ii-isa-bitfields","schema_version":1,"generated":True,"source_files":[str(args.cpp).replace("\\","/")]+[str(p).replace("\\","/") for p in paths],"canonical_abi":{"name":"chimera-ii-host-instruction-v1","bytes":16,"layout":"opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]","bit_order":"little-endian field packing; opcode occupies bits 15:0"},"instruction_count":len(instructions),"instructions":instructions}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(f"generated {args.output}: {len(instructions)} instructions")
if __name__=="__main__": raise SystemExit(main())
