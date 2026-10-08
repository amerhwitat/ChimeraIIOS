#!/usr/bin/env python3
"""Disassemble the current prototype 16-byte Chimera record stream in NCB1 .text."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/binary"))
from chimera_binary import NCB_HEADER,NCB_SECTION,NCB_MAGIC,validate_ncb
NAMES=["NOP","MOV","ADD","SUB","MUL","DIV","AND","OR","XOR","SHL","SHR","CMP","LOAD","STORE","CALL","RET","JMP","CJMP","TCONTRACT","MODEXP","NETSEND","SYSCALL","HALT"]
def main():
 p=argparse.ArgumentParser();p.add_argument("image");a=p.parse_args();data=Path(a.image).read_bytes();meta=validate_ncb(data)
 _,ver,hs,flags,isa,word,count,entry,sto,fs,stack,heap,base,res=NCB_HEADER.unpack_from(data)
 sections=[]
 for i in range(count):
  name,fl,off,size,mem,align=NCB_SECTION.unpack_from(data,sto+i*NCB_SECTION.size)
  sections.append((name.split(b"\0",1)[0].decode("ascii","replace"),fl,off,size,mem))
 print(f"# NCB1 v{ver} ISA={isa} word_bits={word} entry=0x{entry:x} stack={stack} heap_cap={heap}")
 found=False
 for name,fl,off,size,mem in sections:
  if name!=".text":continue
  found=True
  if size%16:raise SystemExit(f".text size {size} is not a multiple of 16-byte prototype records")
  for pc in range(off,off+size,16):
   op=data[pc];width=data[pc+1]
   if op>=len(NAMES) or width>63:raise SystemExit(f"invalid opcode/width at file offset 0x{pc:x}")
   rd=int.from_bytes(data[pc+2:pc+4],"little");r1=int.from_bytes(data[pc+4:pc+6],"little");r2=int.from_bytes(data[pc+6:pc+8],"little");imm=int.from_bytes(data[pc+8:pc+16],"little")
   print(f"{pc-off:08x}: {NAMES[op]} r{rd}, r{r1}, r{r2} ; width={1<<width} imm=0x{imm:x}")
 if not found:raise SystemExit("NCB1 image has no .text section")
if __name__=="__main__":main()
