#!/usr/bin/env python3
"""Build an experimental NCB1 executable from a JSON manifest."""
import argparse,json
from pathlib import Path
from chimera_binary import NCB_HEADER,NCB_SECTION,MAX_SECTIONS,validate_ncb,NCB_MAGIC

def build(manifest_path,output_path):
 m=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
 word=int(m["word_bits"]);isa=int(m.get("isa_id",1));flags=int(m.get("flags",0))
 stack=int(m.get("stack_bytes",1<<20));heap=int(m.get("heap_limit_bytes",1<<30));base=int(m.get("image_base",0))
 sections=m["sections"]
 if not 8<=word<=1048576 or word%8:raise ValueError("word_bits must be byte-aligned 8..1048576")
 if not 1<=len(sections)<=MAX_SECTIONS:raise ValueError("section count out of range")
 table=NCB_HEADER.size;cursor=table+len(sections)*NCB_SECTION.size;records=[];payloads=[];entry=0
 entry_name=m.get("entry_section",".text")
 for s in sections:
  name=str(s["name"]).encode("ascii")
  if len(name)>15:raise ValueError("section name must be at most 15 ASCII bytes")
  fl=int(s.get("flags",4));align=int(s.get("alignment",1))
  if align<1 or align&(align-1):raise ValueError("alignment must be a power of two")
  cursor=(cursor+align-1)&~(align-1)
  if "path" in s:data=Path(s["path"]).read_bytes()
  elif "hex" in s:data=bytes.fromhex(s["hex"])
  else:data=b""
  mem=int(s.get("memory_size",len(data)))
  if mem<len(data):raise ValueError("memory_size cannot be smaller than file data")
  records.append((name,fl,cursor,len(data),mem,align));payloads.append((cursor,data))
  if s["name"]==entry_name:
   off=int(m.get("entry_offset_in_section",0))
   if not fl&1 or not 0<=off<len(data):raise ValueError("entry must be in file-backed executable section")
   entry=cursor+off
  cursor+=len(data)
 if not entry:raise ValueError("entry section missing or invalid")
 out=bytearray(cursor)
 for i,r in enumerate(records):NCB_SECTION.pack_into(out,table+i*NCB_SECTION.size,r[0].ljust(16,b"\0"),*r[1:])
 for off,data in payloads:out[off:off+len(data)]=data
 NCB_HEADER.pack_into(out,0,NCB_MAGIC,1,NCB_HEADER.size,flags,isa,word,len(records),entry,table,len(out),stack,heap,base,0)
 validate_ncb(bytes(out));Path(output_path).write_bytes(out)
 return {"output":str(output_path),"file_size":len(out),"word_bits":word,"sections":len(records),"entry_offset":entry}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("manifest");p.add_argument("output");a=p.parse_args()
 print(json.dumps(build(a.manifest,a.output),indent=2))
if __name__=="__main__":main()
