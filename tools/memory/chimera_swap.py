#!/usr/bin/env python3
"""Finite regular-file swap reference backend; not a kernel page-fault handler."""
import argparse, json, os, struct, zlib
from pathlib import Path
MAGIC=b"CHMSWP1\0";VERSION=1;PAGE=4096
HEADER=struct.Struct("<8sIIQ");META=struct.Struct("<B3xII");MAX_SLOTS=1<<20
class SwapError(ValueError):pass
class SwapArea:
 def __init__(self,path):
  self.path=Path(path);self.file=open(self.path,"r+b");raw=self.file.read(HEADER.size)
  if len(raw)!=HEADER.size:self.file.close();raise SwapError("truncated swap header")
  magic,version,page,slots=HEADER.unpack(raw)
  if magic!=MAGIC or version!=VERSION or page!=PAGE or not 1<=slots<=MAX_SLOTS:self.file.close();raise SwapError("invalid swap header")
  self.slots=slots
  if self.path.stat().st_size!=HEADER.size+slots*(META.size+PAGE):self.file.close();raise SwapError("swap area size mismatch")
 @classmethod
 def create(cls,path,slots):
  if not 1<=slots<=MAX_SLOTS:raise SwapError("slots must be 1..1048576")
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
  with open(path,"xb") as f:
   f.write(HEADER.pack(MAGIC,VERSION,PAGE,slots));zero=META.pack(0,0,0)+bytes(PAGE)
   for _ in range(slots):f.write(zero)
   f.flush();os.fsync(f.fileno())
  return cls(path)
 def offset(self,slot):
  if not isinstance(slot,int) or not 0<=slot<self.slots:raise SwapError("slot out of range")
  return HEADER.size+slot*(META.size+PAGE)
 def write_page(self,slot,data):
  data=bytes(data)
  if len(data)!=PAGE:raise SwapError("page must be exactly 4096 bytes")
  crc=zlib.crc32(data)&0xffffffff;self.file.seek(self.offset(slot));self.file.write(META.pack(1,crc,PAGE));self.file.write(data);self.file.flush()
  return crc
 def read_page(self,slot):
  self.file.seek(self.offset(slot));raw=self.file.read(META.size)
  if len(raw)!=META.size:raise SwapError("truncated slot")
  state,crc,n=META.unpack(raw);data=self.file.read(PAGE)
  if state!=1 or n!=PAGE or len(data)!=PAGE:raise SwapError("slot empty or corrupt")
  if zlib.crc32(data)&0xffffffff!=crc:raise SwapError("page checksum mismatch")
  return data
 def clear(self,slot):
  self.file.seek(self.offset(slot));self.file.write(META.pack(0,0,0)+bytes(PAGE));self.file.flush()
 def close(self):self.file.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest="cmd",required=True);c=s.add_parser("create");c.add_argument("path");c.add_argument("--slots",type=int,required=True);i=s.add_parser("info");i.add_argument("path");a=p.parse_args()
 if a.cmd=="create":x=SwapArea.create(a.path,a.slots);x.close();print(json.dumps({"status":"created","slots":a.slots,"page_bytes":PAGE,"capacity_bytes":a.slots*PAGE}))
 else:x=SwapArea(a.path);print(json.dumps({"status":"valid","slots":x.slots,"page_bytes":PAGE,"capacity_bytes":x.slots*PAGE}));x.close()
if __name__=="__main__":main()
