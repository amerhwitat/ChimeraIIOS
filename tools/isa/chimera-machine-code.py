#!/usr/bin/env python3
"""Identify executable/object formats and route toolchain operations conservatively.

This tool detects file/container architecture and available providers. It does not
claim instruction-set conformance merely because a file header is recognizable.
Foreign execution is limited to an explicitly detected format and installed provider.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(os.environ.get("CHIMERA_ARCH_BACKENDS", ROOT / "tools/isa/architecture-backends.json"))

def registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def host_arch():
    m = platform.machine().lower()
    aliases = {"amd64":"x86_64","x86_64":"x86_64","i386":"x86","i686":"x86",
               "aarch64":"aarch64","arm64":"aarch64","armv7l":"armv7",
               "riscv64":"riscv64","ppc64le":"powerpc64"}
    return aliases.get(m, m or "unknown")

def arch_by_elf(machine, elf_class):
    for name, spec in registry()["architectures"].items():
        if spec.get("elf_machine") == machine and name != "unknown":
            expected = spec.get("elf_class")
            if expected is None or expected == elf_class:
                if machine != 243 or expected == elf_class:
                    return name
    return "unknown"

def identify_bytes(data: bytes, forced_arch: str | None = None):
    out = {"format":"unknown","architecture":"unknown","confidence":"unknown",
           "executable":False,"endianness":"unknown","details":{}}
    if forced_arch:
        aliases = {}
        for name, spec in registry()["architectures"].items():
            aliases[name] = name
            for alias in spec.get("aliases", []): aliases[alias.lower()] = name
        a = aliases.get(forced_arch.lower())
        if not a: raise ValueError(f"architecture is not registered: {forced_arch}")
        out.update(format="raw", architecture=a, confidence="user-specified",
                   details={"warning":"raw bytes have no self-describing architecture header"})
        return out
    if data.startswith(b"\x7fELF"):
        if len(data) < 20: raise ValueError("truncated ELF header")
        cls, enc = data[4], data[5]
        if cls not in (1,2) or enc not in (1,2): raise ValueError("invalid ELF class or endianness")
        endian = "<" if enc == 1 else ">"
        machine = struct.unpack(endian+"H", data[18:20])[0]
        arch = arch_by_elf(machine, cls)
        out.update(format="ELF", architecture=arch, confidence="header",
                   executable=True, endianness="little" if enc == 1 else "big",
                   details={"elf_class":32 if cls==1 else 64,"machine_id":machine})
        return out
    if data[:2] == b"MZ":
        out.update(format="PE-or-DOS-MZ", confidence="signature", executable=True)
        if len(data) >= 64:
            peoff = struct.unpack_from("<I", data, 0x3c)[0]
            if peoff + 6 <= len(data) and data[peoff:peoff+4] == b"PE\0\0":
                machine = struct.unpack_from("<H", data, peoff+4)[0]
                arch = next((n for n,s in registry()["architectures"].items()
                             if any(int(v,16)==machine for v in s.get("pe_machine",[]))), "unknown")
                out.update(format="PE/COFF", architecture=arch, confidence="header",
                           details={"machine_id":f"0x{machine:04x}"})
            else:
                out.update(format="DOS-MZ", architecture="dos-x86", confidence="signature")
        return out
    if len(data) >= 4:
        magic = data[:4]
        macho = {b"\xfe\xed\xfa\xce":("big","32"),b"\xce\xfa\xed\xfe":("little","32"),
                 b"\xfe\xed\xfa\xcf":("big","64"),b"\xcf\xfa\xed\xfe":("little","64")}
        if magic in macho:
            endian,bits=macho[magic]
            if len(data) >= 8:
                cpu=struct.unpack((">" if endian=="big" else "<")+"I",data[4:8])[0]
                arch={7:"x86","0x01000007":"macos-x86_64",12:"armv7","0x0100000c":"macos-aarch64"}.get(cpu,"unknown")
                if cpu == 0x01000007: arch="macos-x86_64"
                if cpu == 0x0100000c: arch="macos-aarch64"
            else: arch="unknown"; cpu=None
            out.update(format="Mach-O",architecture=arch,confidence="header",executable=True,
                       endianness=endian,details={"bits":int(bits),"cpu_type":cpu})
            return out
        if magic in (b"\xca\xfe\xba\xbe",b"\xbe\xba\xfe\xca",b"\xca\xfe\xba\xbf",b"\xbf\xba\xfe\xca"):
            out.update(format="Mach-O-fat",confidence="signature",executable=True,
                       details={"note":"fat/universal binary; inspect per-slice CPU table"})
            return out
    if data.startswith(b"\0asm"):
        out.update(format="WebAssembly",architecture="wasm32",confidence="header",executable=True,
                   details={"note":"version and module validation are separate steps"})
        return out
    if data.startswith(b"UF2\n"):
        out.update(format="UF2-firmware-container",confidence="signature",
                   details={"note":"target requires UF2 block family metadata"})
        return out
    if data.startswith(b":") and data.rstrip().endswith((b"\n",b"\r")):
        lines=data.splitlines()
        if lines and all(line.startswith(b":") and len(line)>=11 for line in lines):
            out.update(format="Intel-HEX",confidence="text-signature",
                       details={"note":"checksums and target metadata require full parser"})
            return out
    if data.startswith(b"#!"):
        first=data.splitlines()[0][:512].decode("utf-8","replace")
        out.update(format="script",confidence="shebang",details={"interpreter":first[2:].strip()})
        return out
    out["details"]["warning"]="unrecognized format; raw bytes require explicit --arch and are never executed by identify"
    return out

def identify(path, forced_arch=None):
    p=Path(path); data=p.read_bytes(); result=identify_bytes(data, forced_arch)
    result.update(path=str(p),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    return result

def providers():
    names=("clang","llvm-mc","llvm-objdump","objdump","qemu-i386","qemu-x86_64","qemu-arm",
           "qemu-aarch64","qemu-riscv32","qemu-riscv64","qemu-mipsel","qemu-ppc","qemu-ppc64le",
           "wine","darling","wasmtime","wasmer","dosbox-x","dosemu")
    return {n:shutil.which(n) is not None for n in names}

def run_command(args):
    return subprocess.run(args,check=False).returncode

def assemble(ns):
    spec=registry()["architectures"].get(ns.arch.lower())
    if not spec or ns.arch.lower()=="unknown": raise ValueError(f"unknown registered target: {ns.arch}")
    target=ns.target or (spec.get("llvm_targets") or [None])[0]
    if not target: raise RuntimeError(f"no assembler target metadata for {ns.arch}")
    clang=shutil.which("clang")
    if clang: return run_command([clang,"--target="+target,"-c",ns.input,"-o",ns.output])
    llvm_mc=shutil.which("llvm-mc")
    if llvm_mc and ns.triple: return run_command([llvm_mc,"-triple",ns.triple,"-filetype=obj",ns.input,"-o",ns.output])
    raise RuntimeError("no suitable assembler provider installed (clang or llvm-mc); no output was fabricated")

def disassemble(ns):
    info=identify(ns.input)
    if info["format"] not in ("ELF","PE/COFF","Mach-O","WebAssembly"):
        raise RuntimeError(f"disassembly requires a recognized object/executable format, got {info['format']}")
    tool=shutil.which("llvm-objdump") or shutil.which("objdump")
    if not tool: raise RuntimeError("llvm-objdump/objdump is not installed")
    return run_command([tool,"-d",ns.input])

def execute(ns):
    info=identify(ns.input,ns.arch)
    fmt,arch=info["format"],info["architecture"]
    if fmt=="ELF":
        if arch==host_arch(): return run_command([ns.input,*ns.args])
        emulator=shutil.which(registry()["architectures"].get(arch,{}).get("qemu_user",""))
        if emulator: return run_command([emulator,ns.input,*ns.args])
        raise RuntimeError(f"foreign ELF architecture {arch}: matching QEMU user emulator is not installed")
    if fmt=="PE/COFF":
        tool=shutil.which("wine")
        if tool: return run_command([tool,ns.input,*ns.args])
        raise RuntimeError("Windows PE recognized but Wine is not installed")
    if fmt=="Mach-O":
        tool=shutil.which("darling")
        if tool: return run_command([tool,ns.input,*ns.args])
        raise RuntimeError("Mach-O recognized but Darling is not installed; compatibility remains unavailable")
    if fmt=="WebAssembly":
        tool=shutil.which("wasmtime") or shutil.which("wasmer")
        if tool: return run_command([tool,ns.input,*ns.args])
        raise RuntimeError("WebAssembly recognized but Wasmtime/Wasmer is not installed")
    if fmt=="DOS-MZ":
        tool=shutil.which("dosbox-x") or shutil.which("dosemu")
        if tool: return run_command([tool,ns.input,*ns.args])
        raise RuntimeError("DOS executable recognized but DOSBox-X/DOSEMU is not installed")
    raise RuntimeError(f"refusing to execute {fmt} / {arch}: no validated execution route")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    i=sub.add_parser("identify"); i.add_argument("input"); i.add_argument("--arch",help="for raw/non-self-describing bytes")
    sub.add_parser("providers")
    a=sub.add_parser("assemble"); a.add_argument("--arch",required=True); a.add_argument("--target"); a.add_argument("--triple"); a.add_argument("-o","--output",required=True); a.add_argument("input")
    d=sub.add_parser("disassemble"); d.add_argument("input")
    e=sub.add_parser("execute"); e.add_argument("input"); e.add_argument("--arch"); e.add_argument("args",nargs=argparse.REMAINDER)
    ns=p.parse_args()
    try:
        if ns.cmd=="identify": print(json.dumps(identify(ns.input,ns.arch),indent=2)); return 0
        if ns.cmd=="providers": print(json.dumps(providers(),indent=2)); return 0
        if ns.cmd=="assemble": return assemble(ns)
        if ns.cmd=="disassemble": return disassemble(ns)
        if ns.cmd=="execute": return execute(ns)
    except (ValueError,RuntimeError,OSError,json.JSONDecodeError) as ex:
        print(f"chimera-machine-code: error: {ex}",file=sys.stderr); return 2
    return 2

if __name__=="__main__": raise SystemExit(main())
