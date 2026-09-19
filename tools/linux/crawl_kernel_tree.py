#!/usr/bin/env python3
"""Recursively inventory a Linux kernel source tree without copying Linux source into Chimera."""
import argparse,json,os
from pathlib import Path
ARCHES=['alpha','arc','arm','arm64','csky','hexagon','loongarch','m68k','microblaze','mips','nios2','openrisc','parisc','powerpc','riscv','s390','sh','sparc','um','x86','xtensa']
SUBSYSTEMS=['arch','block','crypto','drivers','fs','include','init','ipc','kernel','lib','mm','net','rust','security','sound','virt']
EXT={'.c':'c','.h':'header','.S':'asm','.s':'asm','.cpp':'cpp','.cc':'cpp','.cxx':'cpp'}
def main():
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('-o','--output',required=True);a=p.parse_args();root=Path(a.root)
 counts={k:0 for k in EXT.values()}; dirs={}; arch={x:0 for x in ARCHES}; subs={x:0 for x in SUBSYSTEMS}
 for f in root.rglob('*'):
  if not f.is_file(): continue
  typ=EXT.get(f.suffix)
  if typ: counts[typ]+=1
  rel=f.relative_to(root).parts
  if rel:
   top=rel[0]
   if top in subs: subs[top]+=1
   if top=='arch' and len(rel)>1 and rel[1] in arch: arch[rel[1]]+=1
 out={'schema':'chimera-linux-source-inventory-v1','root':str(root),'language_files':counts,'top_level_files':subs,'architecture_files':arch,'files_scanned':sum(counts.values())}
 Path(a.output).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(out,indent=2))
if __name__=='__main__': main()
