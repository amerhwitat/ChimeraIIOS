#!/usr/bin/env python3
"""Hybrid assembler frontend for NASM x86-64 and the implemented RV32I codec subset."""
from __future__ import annotations
import argparse, struct, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RISCV=ROOT/"tools/isa/riscv_codec.py"
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("info")
    a=sub.add_parser("assemble");a.add_argument("--arch",choices=("x86_64","riscv64"),required=True);a.add_argument("--input",required=True);a.add_argument("--output",required=True)
    x=p.parse_args()
    if x.action=="info":
        print("x86_64: NASM ELF64; riscv64: RV32I/RV64-compatible 32-bit instruction subset via riscv_codec.py")
        return 0
    source=Path(x.input);dest=Path(x.output)
    if not source.is_file(): p.error(f"input file does not exist: {source}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    if x.arch=="x86_64":
        cmd=["nasm","-f","elf64","-o",str(dest),str(source)]
        result=subprocess.run(cmd,check=False)
        return result.returncode
    words=[]
    for number,line in enumerate(source.read_text(encoding="utf-8").splitlines(),1):
        text=line.split("#",1)[0].strip()
        if not text: continue
        result=subprocess.run([sys.executable,str(RISCV),"encode",text],text=True,capture_output=True,check=False)
        if result.returncode:
            print(f"chimera-hybrid: line {number}: {result.stderr or result.stdout}",file=sys.stderr);return result.returncode
        words.append(int(result.stdout.strip(),16))
    dest.write_bytes(b"".join(struct.pack("<I",word) for word in words))
    print(f"assembled {len(words)} RV instruction(s) into {dest}")
    return 0
if __name__=="__main__": raise SystemExit(main())
