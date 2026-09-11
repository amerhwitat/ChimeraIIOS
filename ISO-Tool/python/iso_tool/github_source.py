from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re, shutil, subprocess
from .resilient_network import ConnectivityMonitor, retry_when_online
from .source_archive import extract_archive, is_archive_path, download_archive
_GITHUB_RE=re.compile(r"^(?:https?://github\.com/|git@github\.com:)([^/ :]+/[^/]+?)(?:\.git)?/?$")
_GIT_RE=re.compile(r"^(?:https?://|ssh://|git@|git://).+\.git/?$")
_ARCHIVE_RE=re.compile(r"^https?://.+\.(?:zip|tar|tar\.gz|tgz|tar\.bz2|tbz2|tar\.xz|txz)(?:\?.*)?$",re.I)
@dataclass(frozen=True)
class SourceSpec:
    url:str; ref:str=''; submodules:bool=True; retry_interval:float=15.0; retry_forever:bool=True
def clone(spec:SourceSpec,destination:Path,log=None,stop=None)->Path:
    destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True); args=['git','clone'];
    if spec.ref:args+=['--branch',spec.ref]
    if spec.submodules:args+=['--recurse-submodules']
    args += [spec.url,str(destination)]; monitor=ConnectivityMonitor(interval=spec.retry_interval)
    def operation():
        if destination.exists() and any(destination.iterdir()):raise RuntimeError(f'destination is not empty: {destination}')
        subprocess.run(args,check=True,timeout=3600); return destination
    return retry_when_online(operation,monitor,log=log,stop=stop,max_attempts=None if spec.retry_forever else 3)
def archive_url(repository:str,ref:str='main')->str:
    base=repository.rstrip('/'); return f'{base}/archive/refs/heads/{ref}.zip' if ref else f'{base}/archive/refs/heads/main.zip'
def normalize_github_repository(value:str)->str:
    value=value.strip(); match=_GITHUB_RE.match(value)
    if not match:raise ValueError('Enter a GitHub URL, owner/repository, or a local source path.')
    return match.group(1).removesuffix('.git')
def is_github_reference(value:str)->bool:
    try:normalize_github_repository(value);return True
    except ValueError:return False
def is_git_reference(value:str)->bool:
    value=value.strip(); return bool(_GIT_RE.match(value)) or is_github_reference(value)
def is_source_reference(value:str)->bool:
    p=Path(value).expanduser(); return p.is_dir() or p.is_file() or is_git_reference(value) or bool(_ARCHIVE_RE.match(value))
def classify_source(value:str)->str:
    p=Path(value).expanduser()
    if p.is_dir():return 'directory'
    if p.is_file() or is_archive_path(value):return 'archive'
    if is_github_reference(value):return 'github'
    if is_git_reference(value):return 'git'
    raise ValueError(f'Unsupported source reference: {value}')
def repository_url(value:str)->str:return 'https://github.com/'+normalize_github_repository(value)+'.git'
def prepare_source(value:str,destination:Path,branch:str|None=None)->Path:
    raw=value.strip(); local=Path(raw).expanduser(); kind=classify_source(raw)
    if kind=='directory':return local.resolve()
    if kind=='archive':
        archive=local.resolve()
        if not archive.is_file():archive=destination.parent/(Path(raw.split('?',1)[0]).name or 'source.zip'); download_archive(raw,archive)
        if destination.exists() and any(destination.iterdir()):raise FileExistsError(f'source destination is not empty: {destination}')
        return extract_archive(archive,destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() and any(destination.iterdir()):raise FileExistsError(f'Git checkout destination is not empty: {destination}')
    if not shutil.which('git'):raise RuntimeError('Git was not found. Install Git before cloning a source repository.')
    return clone(SourceSpec(repository_url(raw) if is_github_reference(raw) else raw,branch or '',True,retry_forever=False),destination)
def repository_display_name(value:str)->str:return normalize_github_repository(value) if is_github_reference(value) else Path(value).expanduser().stem or value
