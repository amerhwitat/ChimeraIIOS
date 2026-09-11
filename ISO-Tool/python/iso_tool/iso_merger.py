from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
IMAGE_SUFFIXES={'.iso','.img','.bin','.efi'}
def collect_images(root):return sorted(p for p in Path(root).rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
def merge_staging(source,staging,manifest_path):
 source=Path(source).resolve();staging=Path(staging).resolve();shutil.rmtree(staging,ignore_errors=True);staging.mkdir(parents=True);copied=[]
 for p in source.rglob('*'):
  if not p.is_file() or '.git' in p.parts:continue
  rel=p.relative_to(source);d=staging/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);copied.append({'path':str(rel),'sha256':hashlib.sha256(d.read_bytes()).hexdigest(),'bytes':d.stat().st_size})
 m={'schema':1,'source':str(source),'staging':str(staging),'files':copied,'embedded_images':[str(p.relative_to(source)) for p in collect_images(source)]};Path(manifest_path).parent.mkdir(parents=True,exist_ok=True);Path(manifest_path).write_text(json.dumps(m,indent=2));return m
