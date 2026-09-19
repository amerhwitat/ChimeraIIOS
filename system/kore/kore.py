#!/usr/bin/env python3
import json,os,sys
class Kore:
 def __init__(self,m): self.units={u["name"]:u for u in m.get("units",[])}
 def order(self): 
  seen=set();out=[]
  def v(n):
   if n in seen:return
   seen.add(n)
   for d in self.units.get(n,{}).get("requires",[]):v(d)
   out.append(n)
  for n in self.units:v(n)
  return out
if __name__=="__main__":
 p=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),"units.json")
 with open(p,encoding="utf-8") as f:m=json.load(f)
 print(json.dumps({"schema":"kore-runtime-status-v1","boot_order":Kore(m).order(),"units":m["units"]},indent=2))
