"""Windows toolchain detection and optional user-environment configuration."""
from __future__ import annotations
import json, os, shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class ToolSpec:
    name: str
    hints: tuple[str, ...]
    executable: str
    env_var: str

DEFAULT_TOOLS = (
    ToolSpec("GCC/MinGW", (r"C:\MinGW\bin", r"C:\msys64\mingw64\bin", r"C:\msys64\ucrt64\bin"), "gcc.exe", "MINGW_HOME"),
    ToolSpec("MSVC (Visual Studio)", (r"C:\Program Files\Microsoft Visual Studio", r"C:\Program Files (x86)\Microsoft Visual Studio"), "cl.exe", "MSVC_HOME"),
    ToolSpec("NASM Assembler", (r"C:\Program Files\NASM", r"C:\AppData\Local\NASM"), "nasm.exe", "NASM_HOME"),
    ToolSpec("MASM Assembler", (r"C:\Program Files\Microsoft Visual Studio", r"C:\Program Files (x86)\Microsoft Visual Studio"), "ml.exe", "MASM_HOME"),
    ToolSpec("Go Compiler", (r"C:\Program Files\Go\bin", r"C:\Go\bin"), "go.exe", "GOROOT"),
    ToolSpec("Rust Compiler", (r"%USERPROFILE%\.cargo\bin",), "rustc.exe", "RUST_HOME"),
    ToolSpec("Java JDK", (r"C:\Program Files\Java", r"C:\Program Files\Eclipse Adoptium"), "javac.exe", "JAVA_HOME"),
    ToolSpec("Python Interpreter", (r"%USERPROFILE%\AppData\Local\Programs\Python",), "python.exe", "PYTHON_HOME"),
)
AUXILIARY_TOOLS = (
    ToolSpec("LLVM/Clang", (r"C:\Program Files\LLVM\bin",), "clang.exe", "LLVM_HOME"),
    ToolSpec("LLD Linker", (r"C:\Program Files\LLVM\bin",), "lld-link.exe", "LLVM_HOME"),
    ToolSpec("GNU C++", (r"C:\MinGW\bin", r"C:\msys64\mingw64\bin", r"C:\msys64\ucrt64\bin"), "g++.exe", "MINGW_HOME"),
    ToolSpec("GNU Linker", (r"C:\MinGW\bin", r"C:\msys64\mingw64\bin", r"C:\msys64\ucrt64\bin"), "ld.exe", "MINGW_HOME"),
    ToolSpec("CMake", (r"C:\Program Files\CMake\bin",), "cmake.exe", "CMAKE_HOME"),
    ToolSpec("Ninja", (r"C:\Program Files\ninja",), "ninja.exe", "NINJA_HOME"),
    ToolSpec("MSBuild", (r"C:\Program Files\Microsoft Visual Studio",), "MSBuild.exe", "MSBUILD_HOME"),
    ToolSpec("Git", (r"C:\Program Files\Git\cmd",), "git.exe", "GIT_HOME"),
    ToolSpec("xorriso", (r"C:\Program Files\xorriso\bin",), "xorriso.exe", "XORRISO_HOME"),
    ToolSpec("Oscdimg", (r"C:\Program Files\Windows Kits",), "oscdimg.exe", "OSCDIMG_HOME"),
)

def _expand(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))

def _home(exe: Path) -> Path:
    parent = exe.parent.resolve()
    return parent.parent if parent.name.lower() == "bin" else parent

def _vs_roots() -> list[Path]:
    if os.name != "nt": return []
    try:
        import winreg
        roots=[]
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for name in (r"SOFTWARE\Microsoft\VisualStudio\SxS\VS7", r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7"):
                try:
                    with winreg.OpenKey(hive, name) as key:
                        for i in range(winreg.QueryInfoKey(key)[1]):
                            _, value, _ = winreg.EnumValue(key, i)
                            if value: roots.append(Path(value))
                except OSError: pass
        return list(dict.fromkeys(roots))
    except ImportError: return []

def _search(root: Path, executable: str, max_depth: int = 3) -> Path | None:
    if not root.is_dir(): return None
    try:
        base=len(root.resolve().parts)
        for candidate in root.rglob(executable):
            if candidate.is_file() and len(candidate.resolve().parts)-base <= max_depth:
                return candidate.resolve()
    except OSError: pass
    return None

def _find(spec: ToolSpec) -> tuple[Path | None, str | None]:
    found=shutil.which(spec.executable)
    if found: return Path(found).resolve(), "PATH"
    hints=[_expand(x) for x in spec.hints]
    if spec.name.startswith(("MSVC", "MASM")): hints += _vs_roots()
    for hint in hints:
        found=_search(hint, spec.executable)
        if found: return found, "search"
    return None, None

def detect_tools(tools: Iterable[ToolSpec] = DEFAULT_TOOLS + AUXILIARY_TOOLS) -> dict:
    results=[]
    for spec in tools:
        exe,source=_find(spec)
        results.append({**asdict(spec), "hints": list(spec.hints), "status": "found" if exe else "not-found", "executable_path": str(exe) if exe else None, "home": str(_home(exe)) if exe else None, "source": source})
    return {"platform": os.name, "platform_name": os.environ.get("OS", os.name), "tools": results}

def apply_user_environment(report: dict, persist: bool = False) -> dict:
    changes={}; additions=[]; current=os.environ.get("PATH", "")
    entries=current.split(os.pathsep) if current else []
    for tool in report["tools"]:
        if tool["status"] != "found": continue
        if tool["home"]: changes[tool["env_var"]]=tool["home"]
        bindir=str(Path(tool["executable_path"]).parent)
        if not any(os.path.normcase(bindir.rstrip("\\")) == os.path.normcase(x.rstrip("\\")) for x in entries + additions): additions.append(bindir)
    merged=[]; seen=set()
    for x in entries + additions:
        x=x.strip().rstrip("\\"); k=os.path.normcase(x)
        if x and k not in seen: seen.add(k); merged.append(x)
    changes["PATH"]=os.pathsep.join(merged)
    os.environ.update(changes)
    if persist and os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
            for name,value in changes.items(): winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ if "%" in value else winreg.REG_SZ, value)
    return {"changes": changes, "persisted": bool(persist and os.name == "nt"), "new_paths": additions}

def write_report(report: dict, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output
