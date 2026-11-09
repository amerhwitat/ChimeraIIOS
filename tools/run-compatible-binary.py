#!/usr/bin/env python3
"""Inspect a binary and optionally run it with a matching native/compatibility runtime.

Execution is opt-in: use --run. The selected runtime is always printed so that
compatibility/emulation is never misrepresented as native execution.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("chm_binary_headers",ROOT/"tools/inspect-binary-headers.py")
HEADERS=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(HEADERS)

def normalized_host_arch(machine):
    value=machine.lower()
    return {"amd64":"x86_64","x64":"x86_64","aarch64":"AArch64","arm64":"AArch64",
            "armv7l":"ARM","armv6l":"ARM","riscv64":"RISC-V","ppc64le":"PowerPC64",
            "ppc64":"PowerPC64","s390x":"s390","i386":"i386","i686":"i386"}.get(value,machine)

def choose_command(report, path, host=None, which=shutil.which, extra_args=None, sysroot=None):
    host=host or (platform.system(),platform.machine())
    system,machine=host[0],normalized_host_arch(host[1])
    args=list(extra_args or [])
    fmt,arch=report.get("format"),report.get("architecture")
    if fmt=="ELF":
        if system!="Linux":
            raise RuntimeError("Linux ELF execution requires a Linux host or a full Linux VM; CPU emulation alone is not an OS runtime")
        if arch==machine:
            return [str(path),*args],"native-linux"
        qemu={
            "i386":"qemu-i386","x86_64":"qemu-x86_64","ARM":"qemu-arm",
            "AArch64":"qemu-aarch64","RISC-V":"qemu-riscv64","s390":"qemu-s390x",
            "PowerPC":"qemu-ppc","PowerPC64":"qemu-ppc64","MIPS":"qemu-mips",
            "LoongArch":"qemu-loongarch64",
        }
        if arch=="MIPS" and report.get("endianness")=="little": qemu["MIPS"]="qemu-mipsel"
        executable=which(qemu.get(arch,""))
        if not executable: raise RuntimeError(f"No QEMU user-mode runner installed for {arch}")
        command=[executable]
        if sysroot: command.extend(["-L",str(sysroot)])
        return [*command,str(path),*args],"qemu-user"
    if fmt=="PE/COFF":
        if system=="Windows": return [str(path),*args],"native-windows"
        wine=which("wine64") or which("wine")
        if not wine: raise RuntimeError("Windows PE requires Wine on this host")
        return [wine,str(path),*args],"wine-compat"
    if fmt=="Mach-O":
        if system=="Darwin": return [str(path),*args],"native-macos"
        raise RuntimeError("Mach-O execution requires macOS or a full macOS virtual machine; CPU emulation alone is insufficient")
    if fmt=="DOS MZ":
        dosbox=which("dosbox-x") or which("dosbox")
        if not dosbox: raise RuntimeError("DOS MZ execution requires DOSBox or DOSBox-X")
        name=path.name
        if not re.fullmatch(r"[A-Za-z0-9_.-]+",name):
            raise RuntimeError("DOSBox launcher accepts only simple DOS-safe filenames")
        parent=str(path.parent).replace('"','')
        command=f'mount c "{parent}"'
        return [dosbox,"-c",command,"-c","c:","-c",name,"-c","exit"],"dosbox-emulation"
    if fmt=="WebAssembly":
        runtime=which("wasmtime")
        if runtime:return [runtime,"run",str(path),*args],"wasmtime"
        runtime=which("wasmer")
        if runtime:return [runtime,"run",str(path),*args],"wasmer"
        raise RuntimeError("WebAssembly requires Wasmtime or Wasmer")
    if path.suffix.lower()==".jar":
        java=which("java")
        if not java: raise RuntimeError("JAR execution requires a Java runtime")
        return [java,"-jar",str(path),*args],"jvm"
    raise RuntimeError(f"No reviewed execution route for {fmt} ({arch}); file was not run")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary",type=Path)
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--run",action="store_true",help="execute the file (default is inspection only)")
    parser.add_argument("--dry-run",action="store_true",help="show selected runtime command without executing")
    parser.add_argument("--sysroot",type=Path,help="QEMU user-mode sysroot")
    parser.add_argument("--timeout",type=int,default=60)
    parser.add_argument("args",nargs=argparse.REMAINDER,help="arguments passed to the selected runtime after --")
    ns=parser.parse_args()
    path=ns.binary.resolve()
    if not path.is_file(): parser.error(f"not a regular file: {path}")
    report=HEADERS.inspect(path.read_bytes()[:4096])
    output={"path":str(path),**report}
    if not ns.run and not ns.dry_run:
        print(json.dumps(output,indent=2) if ns.json else
              f"{path}: {report['format']} | {report['os']} | {report['architecture']} | {report['bits'] or '?'}-bit")
        return 0
    extra=ns.args[1:] if ns.args[:1]==["--"] else ns.args
    try: command,mode=choose_command(report,path,extra_args=extra,sysroot=ns.sysroot)
    except RuntimeError as exc:
        print(f"Refused: {exc}",file=sys.stderr);return 69
    print(f"execution_mode={mode}",file=sys.stderr)
    print(json.dumps({"execution_mode":mode,"command":command},indent=2))
    if ns.dry_run:return 0
    try:
        return subprocess.run(command,timeout=max(1,ns.timeout),check=False).returncode
    except subprocess.TimeoutExpired:
        print(f"Execution timed out after {ns.timeout}s",file=sys.stderr);return 124

if __name__=="__main__":
    raise SystemExit(main())
