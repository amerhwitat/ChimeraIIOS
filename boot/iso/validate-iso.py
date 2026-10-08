#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

REQUIRED_DIRS = ('boot/spitfire','boot/jasper','boot/koronos','EFI/BOOT','EFI/CHIMERA','chimera','src','checksums')
REQUIRED_FILES = ('boot/spitfire/sf0_mbr.asm','boot/spitfire/sf1_longmode.asm','boot/spitfire/sf2_loader.cpp','boot/jasper/grub.cfg','chimera/README.txt','boot/chimera/manifests/boot-pipeline-contract.json')
CANONICAL_STAGES = ('Spit Fire','Jasper/GRUB','Koronos ELF','hardware/driver initialization','scheduler/runtime loop','live/recovery/installer userspace','Aurora')
OBSOLETE_ARTWORK = ('aurora-background.jpg',)

def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def validate(tree: pathlib.Path):
    missing=[d for d in REQUIRED_DIRS if not (tree/d).is_dir()]
    missing += [f for f in REQUIRED_FILES if not (tree/f).is_file()]
    if missing: raise SystemExit('missing required ISO layout entries: '+', '.join(missing))
    contract_path = tree/'boot/chimera/manifests/boot-pipeline-contract.json'
    try:
        contract = json.loads(contract_path.read_text())
    except Exception as exc:
        raise SystemExit(f'cannot read canonical boot pipeline contract: {exc}')
    stages = tuple(item.get('stage') for item in contract.get('pipeline', []))
    if stages != CANONICAL_STAGES:
        raise SystemExit(f'canonical boot stage order mismatch: {stages!r}')
    if contract.get('kernel_entry') != '/boot/koronos/koronos.elf':
        raise SystemExit('canonical kernel entry must be /boot/koronos/koronos.elf')
    grub = tree/'boot/grub/grub.cfg'
    if grub.is_file():
        grub_text = grub.read_text(errors='replace')
        if 'multiboot2 /boot/koronos/koronos.elf' not in grub_text:
            raise SystemExit('GRUB does not contain the canonical Koronos ELF handoff')
        for obsolete in OBSOLETE_ARTWORK:
            if obsolete in grub_text:
                raise SystemExit(f'obsolete artwork reference in GRUB: {obsolete}')
    for p in tree.rglob('*'):
        if p.is_file() and any(name in p.name for name in OBSOLETE_ARTWORK):
            raise SystemExit(f'obsolete artwork artifact present in ISO: {p.relative_to(tree)}')
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
