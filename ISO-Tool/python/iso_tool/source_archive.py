from __future__ import annotations
import hashlib, shutil, tarfile, urllib.request, zipfile
from pathlib import Path
ARCHIVE_SUFFIXES=('.zip','.tar','.tar.gz','.tgz','.tar.bz2','.tbz2','.tar.xz','.txz')
def sha256_file(path:Path,chunk_size:int=1024*1024)->str:
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(chunk_size),b''): digest.update(chunk)
    return digest.hexdigest()
def is_archive_path(value:str|Path)->bool:
    name=str(value).lower().split('?',1)[0]; return any(name.endswith(s) for s in ARCHIVE_SUFFIXES)
def _safe_destination(root:Path,member_name:str)->Path:
    root=root.resolve(); candidate=(root/member_name).resolve()
    try:candidate.relative_to(root)
    except ValueError as exc:raise ValueError(f'archive path traversal rejected: {member_name}') from exc
    return candidate
def extract_archive(archive:Path,destination:Path)->Path:
    archive=Path(archive).resolve(); destination=Path(destination).resolve(); destination.mkdir(parents=True,exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target=_safe_destination(destination,member.filename)
                if member.is_dir(): target.mkdir(parents=True,exist_ok=True); continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(member) as source,target_stream:=target.open('wb'): shutil.copyfileobj(source,target_stream)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                target=_safe_destination(destination,member.name)
                if member.issym() or member.islnk(): raise ValueError(f'archive link rejected: {member.name}')
                if member.isdir(): target.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True,exist_ok=True); extracted=bundle.extractfile(member)
                    if extracted is None: raise ValueError(f'cannot extract archive member: {member.name}')
                    with extracted,target.open('wb') as output: shutil.copyfileobj(extracted,output)
                else: raise ValueError(f'unsupported archive member: {member.name}')
    else: raise ValueError(f'unsupported source archive: {archive}')
    roots=list(destination.iterdir()); return roots[0] if len(roots)==1 and roots[0].is_dir() else destination
def download_archive(url:str,destination:Path,timeout:int=120)->dict:
    destination=Path(destination).resolve(); destination.parent.mkdir(parents=True,exist_ok=True); request=urllib.request.Request(url,headers={'User-Agent':'Chimera-II-ISO-Tool/1.0'})
    with urllib.request.urlopen(request,timeout=timeout) as response,destination.open('wb') as output: shutil.copyfileobj(response,output)
    return {'url':url,'path':str(destination),'sha256':sha256_file(destination),'size':destination.stat().st_size}
