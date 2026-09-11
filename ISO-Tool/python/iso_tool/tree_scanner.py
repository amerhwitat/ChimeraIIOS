from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import hashlib,json,os
SOURCE_EXTENSIONS={'.c':'C','.h':'C/C++ header','.cc':'C++','.cpp':'C++','.cxx':'C++','.hpp':'C++ header','.asm':'Assembly','.s':'Assembly','.S':'Assembly','.inc':'Assembly include','.rs':'Rust','.go':'Go','.java':'Java','.kt':'Kotlin','.kts':'Kotlin','.py':'Python','.js':'JavaScript','.mjs':'JavaScript','.cjs':'JavaScript','.ts':'TypeScript','.tsx':'TypeScript','.cs':'C#','.swift':'Swift','.f':'Fortran','.f90':'Fortran','.f95':'Fortran','.f03':'Fortran','.m':'Objective-C','.mm':'Objective-C++','.zig':'Zig','.d':'D','.lua':'Lua','.sh':'Shell','.ps1':'PowerShell','.bat':'Batch','.cmd':'Batch'}
BUILD_NAMES={'CMakeLists.txt','Makefile','makefile','GNUmakefile','meson.build','Cargo.toml','package.json','pyproject.toml','setup.py','pom.xml','build.gradle','build.gradle.kts','go.mod'}
IMAGE_EXTENSIONS={'.iso':'ISO','.img':'disk image','.bin':'binary image','.efi':'UEFI executable','.wim':'Windows image','.vhd':'virtual disk','.vhdx':'virtual disk','.qcow2':'virtual disk'}
@dataclass
class Entry:path:str;kind:str;size:int=0;sha256:str|None=None;language:str|None=None;children:list|None=None
def _sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()
def _kind(p:Path):
    if p.name in BUILD_NAMES or p.suffix.lower() in {'.sln','.vcxproj','.csproj','.fsproj','.pro','.pri'}:return 'build-system',None
    if p.name.lower().startswith(('readme','license','notice','changelog')) or p.suffix.lower() in {'.md','.rst','.txt','.adoc'}:return 'document',None
    if p.suffix.lower() in IMAGE_EXTENSIONS:return 'image',IMAGE_EXTENSIONS[p.suffix.lower()]
    if p.suffix in SOURCE_EXTENSIONS:return 'source',SOURCE_EXTENSIONS[p.suffix]
    if p.suffix.lower() in {'.dll','.so','.dylib','.a','.lib','.o','.obj','.exe'}:return 'artifact',None
    return 'file',None
def scan_tree(root:Path,manifest_path:Path|None=None)->dict:
    root=Path(root).resolve();languages={};counts={};builds=[];images=[];scripts=[]
    def walk(p:Path):
        rel='.' if p==root else str(p.relative_to(root)).replace(os.sep,'/')
        if p.is_symlink():return Entry(rel,'symlink',size=p.lstat().st_size)
        if p.is_dir():return Entry(rel,'directory',children=[walk(x) for x in sorted(p.iterdir(),key=lambda q:(not q.is_dir(),q.name.lower()))])
        kind,lang=_kind(p);counts[kind]=counts.get(kind,0)+1
        if lang:languages[lang]=languages.get(lang,0)+1
        if kind=='build-system':builds.append(rel)
        if kind=='image':images.append(rel)
        if p.suffix.lower() in {'.sh','.ps1','.bat','.cmd'}:scripts.append(rel)
        return Entry(rel,kind,p.stat().st_size,_sha(p),lang)
    tree=walk(root);result={'root':str(root),'tree':asdict(tree),'summary':{'files':sum(counts.values()),'by_kind':counts,'languages':languages,'build_files':builds,'images':images,'scripts_requiring_review':scripts}}
    if manifest_path:Path(manifest_path).parent.mkdir(parents=True,exist_ok=True);Path(manifest_path).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
