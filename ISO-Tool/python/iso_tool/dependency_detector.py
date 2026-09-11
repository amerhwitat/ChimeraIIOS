"""Host dependency inventory shared by every ISO-Tool frontend."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json, os, shutil, subprocess, sys
from pathlib import Path

@dataclass
class Dependency:
    name: str; commands: tuple[str, ...]; required: bool=False; category: str="toolchain"; path: str|None=None; version: str|None=None; status: str="missing"; detail: str=""

DEFAULTS=[Dependency("git",("git",),True,"source"),Dependency("python",("python","python3"),True,"runtime"),Dependency("cmake",("cmake",),True,"build"),Dependency("gcc",("gcc",),False,"compiler"),Dependency("g++",("g++",),False,"compiler"),Dependency("msvc",("cl",),False,"compiler"),Dependency("clang",("clang",),False,"compiler"),Dependency("lld",("lld",),False,"linker"),Dependency("nasm",("nasm",),False,"assembler"),Dependency("masm",("ml","ml64"),False,"assembler"),Dependency("ninja",("ninja",),False,"build"),Dependency("msbuild",("msbuild",),False,"build"),Dependency("make",("make",),False,"build"),Dependency("xorriso",("xorriso","xorrisofs"),False,"image"),Dependency("oscdimg",("oscdimg",),False,"image"),Dependency("qemu",("qemu-system-x86_64",),False,"verification"),Dependency("7zip",("7z","7zz"),False,"archive"),Dependency("zip",("zip",),False,"archive"),Dependency("node",("node",),False,"runtime"),Dependency("npm",("npm",),False,"runtime"),Dependency("java",("java",),False,"runtime"),Dependency("javac",("javac",),False,"compiler"),Dependency("dotnet",("dotnet",),False,"runtime"),Dependency("go",("go",),False,"compiler"),Dependency("rustc",("rustc",),False,"compiler")]

def _version(exe):
    for arg in ("--version","-version"):
        try:
            p=subprocess.run([exe,arg],text=True,capture_output=True,timeout=5); lines=(p.stdout or p.stderr).splitlines()
            if lines:return lines[0].strip()
        except (OSError,subprocess.SubprocessError):pass
    return None

def detect(extra=None):
    deps=DEFAULTS+list(extra or [])
    for d in deps:
        for command in d.commands:
            found=shutil.which(command)
            if found:d.path,d.version,d.status=found,_version(found),"found";break
        if d.status!="found" and d.required:d.detail="Required dependency is not on PATH."
    return {"platform":sys.platform,"python":sys.version.split()[0],"path":os.environ.get("PATH",""),"dependencies":[asdict(d) for d in deps],"summary":{"found":sum(d.status=="found" for d in deps),"missing":sum(d.status=="missing" for d in deps),"required_missing":sum(d.status=="missing" and d.required for d in deps)}}

def write_report(output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(detect(),indent=2),encoding="utf-8");return output
