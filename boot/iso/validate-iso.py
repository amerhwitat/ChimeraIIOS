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
    # Current smoke images carry ring-3 handoff probes, not production target
    # userspaces. Verify an explicit status manifest and its ELF hashes.
    status_path = tree / 'boot/targets/target-runtime-status.json'
    if not status_path.is_file():
        raise SystemExit('missing target runtime status manifest: boot/targets/target-runtime-status.json')
    try:
        status = json.loads(status_path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise SystemExit(f'invalid target runtime status manifest: {exc}')
    if status.get('schema') != 'koronos-target-runtime-status/v1':
        raise SystemExit('unsupported target runtime status schema')
    if status.get('production_ready') is not False:
        raise SystemExit('smoke target payloads must not be marked production_ready')
    expected = {
        'live': ('ring3-console-smoke-probe', 'target-init-live.elf'),
        'installer': ('storage-plan-dry-run-probe', 'target-init-installer.elf'),
        'recovery': ('ring3-diagnostics-only-probe', 'target-init-recovery.elf'),
    }
    targets = status.get('targets')
    if not isinstance(targets, dict) or set(targets) != set(expected):
        raise SystemExit('target runtime status must describe exactly live, installer, and recovery')
    for name, (scope, elf_name) in expected.items():
        entry = targets[name]
        elf = tree / 'boot/targets' / elf_name
        if entry.get('production_ready') is not False or entry.get('scope') != scope:
            raise SystemExit(f'{name}: target payload classification mismatch')
        if entry.get('elf') != elf_name or not elf.is_file():
            raise SystemExit(f'{name}: target ELF missing or mismatched')
        if entry.get('bytes') != elf.stat().st_size or entry.get('sha256') != sha256(elf):
            raise SystemExit(f'{name}: target ELF size/SHA-256 mismatch')
    files=[]
    for p in sorted(tree.rglob('*')):
        if p.is_file() and 'checksums' not in p.parts:
            files.append({'path':p.relative_to(tree).as_posix(),'size':p.stat().st_size,'sha256':sha256(p)})
    return {'format':'chimera-iso-layout-v2','media':'iso9660-el-torito','boot':['bios-multiboot2','uefi-when-available'],'target_runtime_classification':'structured-boot-and-ring3-handoff-smoke-only','production_ready':False,'files':files}

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
