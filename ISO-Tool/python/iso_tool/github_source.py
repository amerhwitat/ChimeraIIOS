from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re, shutil, subprocess

_GITHUB_RE=re.compile(r"^(?:https?://github\.com/|git@github\.com:)([^/ :]+/[^/]+?)(?:\.git)?/?$")
@dataclass(frozen=True)
class SourceSpec:
    url:str; ref:str=''; submodules:bool=True

def normalize_github_repository(value:str)->str:
    m=_GITHUB_RE.match(value.strip())
    if not m: raise ValueError('Enter a GitHub URL, owner/repository, or a local source path.')
    return m.group(1).removesuffix('.git')
def is_github_reference(value:str)->bool:
    try: normalize_github_repository(value); return True
    except ValueError: return False
def repository_url(value:str)->str: return 'https://github.com/'+normalize_github_repository(value)+'.git'
def prepare_source(value:str,destination:Path,branch:str|None=None)->Path:
    raw=value.strip(); local=Path(raw).expanduser()
    if local.is_dir(): return local.resolve()
    if not is_github_reference(raw): raise FileNotFoundError(f'Local repository does not exist: {local}')
    if destination.exists() and any(destination.iterdir()): return destination.resolve()
    git=shutil.which('git')
    if not git: raise RuntimeError('Git was not found.')
    destination.parent.mkdir(parents=True,exist_ok=True); cmd=[git,'clone','--depth','1']
    if branch: cmd += ['--branch',branch]
    cmd += [repository_url(raw),str(destination)]; subprocess.run(cmd,check=True,timeout=1800)
    return destination.resolve()
