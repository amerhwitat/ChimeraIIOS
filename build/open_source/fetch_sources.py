#!/usr/bin/env python3
from __future__ import annotations
import hashlib, ssl, urllib.request
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES=512*1024*1024

def fetch(url:str,destination:Path,sha256:str|None=None,allowed_hosts:tuple[str,...]=('github.com','gitlab.gnome.org','gitlab.freedesktop.org','code.qt.io','code.videolan.org','openprinting.github.io')):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in allowed_hosts: raise ValueError('source host is not allowlisted')
    destination.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(); total=0
    context=ssl.create_default_context()
    with urllib.request.urlopen(url,context=context,timeout=30) as response, destination.open('wb') as out:
        while True:
            chunk=response.read(1024*1024)
            if not chunk: break
            total+=len(chunk)
            if total>MAX_BYTES: raise ValueError('artifact exceeds staging limit')
            digest.update(chunk); out.write(chunk)
    if sha256 and digest.hexdigest().lower()!=sha256.lower():
        destination.unlink(missing_ok=True); raise ValueError('sha256 mismatch')
    return digest.hexdigest()
