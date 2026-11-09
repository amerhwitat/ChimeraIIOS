#!/usr/bin/env python3
"""Select a compatible runtime for an explicitly chosen binary; dry-run unless --run is given."""
from __future__ import annotations
import argparse, importlib.util, platform, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("chm_binary_inspector",ROOT/"tools/inspect-binary-headers.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def choose(path:Path,info:dict):
 fmt,arch=info.get("format"),info.get("architecture"); host=platform.machine().lower()
 if fmt=="ELF":
  native={"amd64":"x86_64","x86_64":"x86_64","aarch64":"AArch64","arm64":"AArch64","i386":"i386","i686":"i386"}.get(host,host)
  if arch.lower()==native.lower(): return [str(path)]
  qemu={"x86_64":"qemu-x86_64","i386":"qemu-i386","AArch64":"qemu-aarch64","ARM":"qemu-arm","RISC-V":"qemu-riscv64","PowerPC64":"qemu-ppc64le","s390":"qemu-s390x"}.get(arch)
  if qemu and shutil.which(qemu): return [shutil.which(qemu),str(path)]
  raise RuntimeError(f"no registered user-mode emulator for ELF architecture {arch}")
 if fmt=="PE/COFF":
  if platform.system()=="Windows": return [str(path)]
  wine=shutil.which("wine") or shutil.which("wine64")
  if wine: return [wine,str(path)]
  raise RuntimeError("Wine runtime is not installed")
 if fmt=="DOS MZ":
  dosbox=shutil.which("dosbox-staging") or shutil.which("dosbox")
  if dosbox: return [dosbox,"-c",f"mount c {path.parent}","-c","c:","-c",path.name]
  raise RuntimeError("DOSBox runtime is not installed")
 if fmt in ("Mach-O","Mach-O Universal"):
  if platform.system()=="Darwin": return [str(path)]
  darling=shutil.which("darling")
  if darling: return [darling,"shell","--",str(path)]
  raise RuntimeError("Darling runtime is not installed for macOS binaries on Linux")
 if fmt=="WebAssembly":
  runtime=shutil.which("wasmtime") or shutil.which("wasmer")
  if runtime: return [runtime,str(path)]
  raise RuntimeError("Wasmtime/Wasmer runtime is not installed")
 raise RuntimeError(f"unsupported or non-executable format: {fmt}")
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("binary",type=Path); p.add_argument("--run",action="store_true")
 p.add_argument("args",nargs=argparse.REMAINDER); a=p.parse_args(); path=a.binary.resolve()
 if not path.is_file(): p.error(f"not a file: {path}")
 with path.open("rb") as f: info=mod.inspect(f.read(4096))
 try: command=choose(path,info)
 except RuntimeError as exc: print(f"compat: {exc}",file=sys.stderr); return 127
 command.extend(a.args); print("Selected runtime:", " ".join(command))
 if not a.run: print("Dry run only; pass --run to execute this explicitly selected file."); return 0
 return subprocess.run(command,check=False).returncode
if __name__=="__main__": raise SystemExit(main())
