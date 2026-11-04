#!/usr/bin/env python3
"""CHMRG01 binary registry hive builder/verifier; Python standard library only."""
import argparse,json,pathlib,struct,sys,zlib
MAGIC=b"CHMRG01\0"; H=struct.Struct("<8sHHIIIIQII"); R=struct.Struct("<HBBI")
T={"u32":1,"u64":2,"bool":3,"string":4,"bytes":5}
def encode(s):
 if s.get("schema_version")!=1: raise ValueError("unsupported schema version")
 es=s.get("entries")
 if not isinstance(es,list) or len(es)>4096: raise ValueError("invalid entry count")
 seen=set(); payload=[]
 for e in es:
  p=e["path"]; t=e["type"]; v=e["value"]
  if not isinstance(p,str) or not p or p.lower()!=p or p.startswith("/") or ".." in p.split("/") or "\0" in p: raise ValueError("invalid canonical path")
  pb=p.encode("utf-8")
  if len(pb)>255 or p in seen: raise ValueError("duplicate or oversized path")
  seen.add(p)
  if t not in T: raise ValueError("unknown value type")
  if t=="u32": vb=struct.pack("<I",int(v))
  elif t=="u64": vb=struct.pack("<Q",int(v))
  elif t=="bool":
   if not isinstance(v,bool): raise ValueError("bool value required")
   vb=bytes([int(v)])
  elif t=="string": vb=str(v).encode("utf-8")
  else: vb=bytes.fromhex(v)
  if len(vb)>1<<20: raise ValueError("value too large")
  payload.append(R.pack(len(pb),T[t],0,len(vb))+pb+vb)
 body=b"".join(payload); total=H.size+len(body); gen=int(s.get("generation",1))
 if not 0<=gen<1<<64: raise ValueError("generation out of range")
 pc=zlib.crc32(body)&0xffffffff
 h=H.pack(MAGIC,1,0,H.size,total,len(es),gen,pc,0,0)
 hc=zlib.crc32(h[:36])&0xffffffff
 return H.pack(MAGIC,1,0,H.size,total,len(es),gen,pc,hc,0)+body
def verify(b):
 if len(b)<H.size: raise ValueError("truncated header")
 magic,maj,minor,hs,total,count,gen,pc,hc,res=H.unpack_from(b)
 if (magic,maj,minor,hs,res)!=(MAGIC,1,0,H.size,0) or total!=len(b) or count>4096: raise ValueError("invalid header")
 if zlib.crc32(b[H.size:])&0xffffffff!=pc or zlib.crc32(b[:36])&0xffffffff!=hc: raise ValueError("CRC mismatch")
 off=H.size; seen=set()
 for _ in range(count):
  if off+R.size>total: raise ValueError("truncated record")
  plen,typ,flags,vlen=R.unpack_from(b,off); off+=R.size
  if not 0<plen<=255 or typ not in T.values() or flags or vlen>1<<20 or off+plen+vlen>total: raise ValueError("invalid record bounds")
  p=b[off:off+plen].decode("utf-8"); off+=plen
  if p.lower()!=p or p.startswith("/") or ".." in p.split("/") or p in seen: raise ValueError("invalid/duplicate path")
  seen.add(p); v=b[off:off+vlen]; off+=vlen
  if (typ==3 and (vlen!=1 or v[0]>1)) or (typ==1 and vlen!=4) or (typ==2 and vlen!=8): raise ValueError("invalid scalar")
 if off!=total: raise ValueError("trailing bytes")
 return {"entries":count,"generation":gen,"bytes":total}
def main():
 a=argparse.ArgumentParser(); s=a.add_subparsers(dest="cmd",required=True)
 b=s.add_parser("build"); b.add_argument("--input",required=True); b.add_argument("--output",required=True)
 v=s.add_parser("verify"); v.add_argument("hive"); x=a.parse_args()
 try:
  if x.cmd=="build":
   d=encode(json.loads(pathlib.Path(x.input).read_text())); o=pathlib.Path(x.output); o.parent.mkdir(parents=True,exist_ok=True)
   t=o.with_suffix(o.suffix+".tmp"); t.write_bytes(d); t.replace(o); print("registry-hive: wrote",o,len(d),"bytes")
  else: print("registry-hive: valid",json.dumps(verify(pathlib.Path(x.hive).read_bytes()),sort_keys=True))
 except (OSError,ValueError,KeyError,TypeError,UnicodeError,struct.error) as e:
  print("registry-hive: ERROR:",e,file=sys.stderr); return 1
 return 0
if __name__=="__main__": raise SystemExit(main())
