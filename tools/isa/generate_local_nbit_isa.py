#!/usr/bin/env python3
"""Generate Chimera II's local N-bit ISA profiles from RISC/CISC source descriptors.

The generator never claims that a width is physically native on a host CPU.
hardware_native is reserved for widths backed by an explicitly supplied local
hardware descriptor. Other widths are legal Chimera software/synthesized
register widths.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

DEFAULT_WIDTHS=[8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536]
FOREIGN=[
    ("x86","CISC",[8,16,32,64]),("aarch64","RISC",[32,64,128]),
    ("riscv","RISC",[32,64,128]),("mips","RISC",[32,64]),
    ("power","RISC",[32,64,128]),("sparc","RISC",[32,64]),("s390","CISC",[32,64])
]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--widths",default=",".join(map(str,DEFAULT_WIDTHS)))
    ap.add_argument("--canonical",type=Path,default=Path("tools/isa/chimera_r8192_opcode_index.csv"))
    args=ap.parse_args()
    widths=[int(x) for x in args.widths.split(",") if x.strip()]
    if any(w<8 or w>65536 or w%8 for w in widths): raise SystemExit("widths must be byte-aligned and in 8..65536")
    native={64,8192}
    profiles=[]
    for w in widths:
        profiles.append({"name":f"chimera-risc-n{w}","source":"chimera-local","style":"RISC","register_bits":w,"min_register_bits":8,"max_register_bits":max(widths),"hardware_native":w in native,
                         "format":{"opcode_bits":16,"register_index_bits":16,"immediate_bits":w,"min_instruction_bytes":16,"max_instruction_bytes":16,"variable_length":False}})
        profiles.append({"name":f"chimera-cisc-n{w}","source":"chimera-local","style":"CISC","register_bits":w,"min_register_bits":8,"max_register_bits":max(widths),"hardware_native":w in native,
                         "format":{"opcode_bits":16,"register_index_bits":16,"immediate_bits":w,"min_instruction_bytes":1,"max_instruction_bytes":32,"variable_length":True}})
    for name,style,ws in FOREIGN:
        for w in ws:
            profiles.append({"name":f"{name}-import-n{w}","source":name,"style":style,"register_bits":w,"min_register_bits":min(ws),"max_register_bits":max(ws),"hardware_native":True,
                             "format":{"opcode_bits":8 if name=="x86" else 32,"register_index_bits":4 if name=="x86" else 5,"immediate_bits":64,"min_instruction_bytes":1,"max_instruction_bytes":15 if name=="x86" else 4,"variable_length":name in {"x86","riscv"}})
    doc={"schema":"chimera-ii-local-nbit-isa-v1","generated":True,"canonical_opcode_source":str(args.canonical).replace("\\","/"),"register_widths_bits":widths,"foreign_sources":[x[0] for x in FOREIGN],"profiles":profiles}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    print(f"generated {args.output}: {len(profiles)} profiles")
if __name__=="__main__":main()
