"""Trusted dependency download/cache/install helpers for ISO-Tool."""
from __future__ import annotations
from pathlib import Path
import os, shutil, urllib.request
NASM_VERSION = "3.02"
NASM_OFFICIAL_BASE = "https://www.nasm.us/pub/nasm/releasebuilds/3.02/win64/"

def downloads_root() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads" / "Chimera-II-ISO-Tool" / "dependencies"

def dependency_folder(name: str) -> Path:
    path = downloads_root() / name; path.mkdir(parents=True, exist_ok=True); return path

def find_nasm() -> str | None:
    exe = shutil.which("nasm")
    if exe: return exe
    for p in [Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "NASM" / "nasm.exe", Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "NASM" / "nasm.exe"]:
        if p.exists(): return str(p)
    return None

def download_nasm(show_folder_callback=None) -> Path:
    folder = dependency_folder("nasm")
    archive = folder / f"nasm-{NASM_VERSION}-win64.zip"
    if not archive.exists(): urllib.request.urlretrieve(NASM_OFFICIAL_BASE + archive.name, archive)
    if show_folder_callback: show_folder_callback(folder)
    return archive

def install_nasm(archive: Path, show_folder_callback=None) -> str:
    import zipfile
    extract = archive.parent / "installed"; extract.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf: zf.extractall(extract)
    matches = list(extract.rglob("nasm.exe"))
    if not matches: raise RuntimeError(f"Downloaded NASM archive contains no nasm.exe: {archive}")
    if show_folder_callback: show_folder_callback(archive.parent)
    return str(matches[0])

def ensure_nasm(show_folder_callback=None, install=True) -> str:
    existing = find_nasm()
    if existing: return existing
    archive = download_nasm(show_folder_callback=show_folder_callback)
    if not install: raise RuntimeError(f"NASM was downloaded to {archive.parent}; automatic installation is disabled")
    return install_nasm(archive, show_folder_callback=show_folder_callback)
