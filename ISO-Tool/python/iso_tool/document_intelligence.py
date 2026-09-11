from __future__ import annotations
import hashlib,json,re
from pathlib import Path
TEXT_EXTENSIONS={'.md','.markdown','.txt','.rst','.adoc','.json','.yaml','.yml','.toml','.ini','.cfg','.cmake','.mk','.c','.cc','.cpp','.cxx','.h','.hpp','.s','.asm','.inc','.rc','.ld','.bat','.cmd','.ps1','.sh','.py','.java','.rs','.go','.js','.ts','.cs','.sln','.vcxproj','.props','.targets','.xml'}
KEYWORDS=('cmake','make','compile','compiler','link','linker','boot','bootloader','kernel','driver','efi','uefi','iso','img','filesystem','library','executable','dependency','build')
def scan_repository(root):
 root=Path(root).resolve();docs=[];files=[]
 for p in sorted(root.rglob('*')):
  if not p.is_file() or '.git' in p.parts:continue
  files.append(str(p.relative_to(root)))
  if p.suffix.lower() not in TEXT_EXTENSIONS and p.name not in {'Makefile','CMakeLists.txt','Dockerfile'}:continue
  try:t=p.read_text(encoding='utf-8',errors='replace')
  except OSError:continue
  docs.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(t.encode()).hexdigest(),'keywords':[k for k in KEYWORDS if re.search(r'\b'+re.escape(k)+r'\b',t,re.I)]})
 return {'root':str(root),'file_count':len(files),'document_count':len(docs),'files':files,'documents':docs}
def infer_components(index):
 n=' '.join(x['path'].lower() for x in index['documents']);h=lambda *x:any(i in n for i in x)
 return {'boot':h('boot','uefi','grub','spit'),'kernel':h('kernel','koronos'),'drivers':h('driver'),'libraries':h('lib','library'),'applications':h('app','application','bin'),'filesystem':h('filesystem','xfs','zfs','ntfs','fat'),'build_system':h('cmakelists.txt','makefile','vcxproj','sln')}
