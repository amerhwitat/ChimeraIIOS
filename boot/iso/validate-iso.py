#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

REQUIRED_DIRS = ('boot/spitfire','boot/jasper','boot/koronos','EFI/BOOT','EFI/CHIMERA','chimera','src','checksums')
REQUIRED_FILES = ('boot/spitfire/sf0_mbr.asm','boot/spitfire/sf1_longmode.asm','boot/spitfire/sf2_loader.cpp','boot/jasper/grub.cfg','chimera/README.txt')

def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def validate(tree: pathlib.Path):
    missing=[d for d in REQUIRED_DIRS if not (tree/d).is_dir()]
    missing += [f for f in REQUIRED_FILES if not (tree/f).is_file()]
    if missing: raise SystemExit('missing required ISO layout entries: '+', '.join(missing))
    files=[]
    for p in sorted(tree.rglob('*')):
        if p.is_file() and 'checksums' not in p.parts:
            files.append({'path':p.relative_to(tree).as_posix(),'size':p.stat().st_size,'sha256':sha256(p)})
    return {'format':'chimera-iso-layout-v2','media':'iso9660-el-torito','boot':['bios-multiboot2','uefi-when-available'],'files':files}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tree',required=True); ap.add_argument('--write-manifest'); ap.add_argument('--json',action='store_true'); a=ap.parse_args()
    manifest=validate(pathlib.Path(a.tree))
    if a.write_manifest:
        out=pathlib.Path(a.write_manifest); out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text('\n'.join(f"{x['sha256']}  {x['path']}" for x in manifest['files'])+'\n')
        meta=out.with_suffix('.json'); meta.write_text(json.dumps(manifest,indent=2)+'\n')
    if a.json: print(json.dumps(manifest,indent=2))
    else: print(f"validated {len(manifest['files'])} staged files")
if __name__=='__main__': main()
