"""Canonical ISO staging/merge utilities."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
IMAGE_SUFFIXES={'.iso','.img','.bin','.efi'}
def collect_images(root:Path):return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
def _copy_tree(source:Path,staging:Path,prefix:Path,copied:list):
    if not source.exists():return
    for p in source.rglob('*'):
        if not p.is_file():continue
        rel=prefix/p.relative_to(source);dst=staging/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);copied.append({'path':str(rel),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size})
def merge_staging(source:Path,staging:Path,manifest_path:Path,artifact_roots:dict|None=None)->dict:
    source=source.resolve();staging=staging.resolve();shutil.rmtree(staging,ignore_errors=True);staging.mkdir(parents=True);copied=[];_copy_tree(source,staging,Path('.'),copied)
    artifact_roots=artifact_roots or {'executables':staging.parent/'binaries'/'executables','libraries':staging.parent/'binaries'/'libraries','boot_images':staging.parent/'boot-images'}
    if artifact_roots.get('executables'):_copy_tree(Path(artifact_roots['executables']),staging,Path('bin'),copied)
    if artifact_roots.get('libraries'):_copy_tree(Path(artifact_roots['libraries']),staging,Path('lib'),copied)
    if artifact_roots.get('boot_images'):_copy_tree(Path(artifact_roots['boot_images']),staging,Path('boot-images'),copied)
    manifest={'schema':2,'source':str(source),'staging':str(staging),'files':copied,'embedded_images':[str(p.relative_to(source)) for p in collect_images(source)],'artifact_roots':{k:str(v) for k,v in artifact_roots.items()}}
    manifest_path.parent.mkdir(parents=True,exist_ok=True);manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8');return manifest
