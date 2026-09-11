"""Dual C++ compiler discovery and optional MSYS2/UCRT64 GCC provisioning."""
from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path

def find_gxx():
    for name in ("g++.exe", "g++", "x86_64-w64-mingw32-g++.exe"):
        hit=shutil.which(name)
        if hit:return hit
    for root in (Path(os.environ.get("LOCALAPPDATA","")), Path(os.environ.get("USERPROFILE",""))/"Downloads"):
        if root.exists():
            hits=list(root.glob("**/ucrt64/bin/g++.exe"))+list(root.glob("**/mingw64/bin/g++.exe"))
            if hits:return str(hits[0])
    return None

def find_msvc():
    for name in ("cl.exe","cl"):
        hit=shutil.which(name)
        if hit:return hit
    roots=[Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Microsoft Visual Studio",Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Microsoft Visual Studio"]
    for root in roots:
        if root.exists():
            hits=list(root.rglob("Hostx64/x64/cl.exe"))
            if hits:return str(hits[0])
    return None

def compiler_report(): return {"gnu_cxx":find_gxx(),"msvc":find_msvc()}

def gcc_install_plan():
    return {"provider":"MSYS2","environment":"UCRT64","package":"mingw-w64-ucrt-x86_64-gcc","command":"pacman -S --needed mingw-w64-ucrt-x86_64-gcc","cache":str(Path(os.environ.get("USERPROFILE","~"))/"Downloads"/"Chimera-II-ISO-Tool"/"dependencies"/"msys2"),"official":"https://www.msys2.org/"}

def run_gcc_version(executable):
    try:
        p=subprocess.run([executable,"--version"],capture_output=True,text=True,timeout=10)
        return (p.stdout or p.stderr).splitlines()[0].strip()
    except (OSError,subprocess.SubprocessError): return "unknown"
