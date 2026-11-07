#!/usr/bin/env python3
"""Cross-build the POSIX command multicall for supported Linux userspace ABIs."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TARGETS={
 "x86_64":{"compiler":"cc","machine":"Advanced Micro Devices X86-64","elf_machine":62,"zig_target":"x86_64-linux-musl"},
 "i686":{"compiler":"i686-linux-gnu-gcc","machine":"Intel 80386","elf_machine":3,"zig_target":"i386-linux-musl"},
 "armel":{"compiler":"arm-linux-gnueabi-gcc","machine":"ARM","elf_machine":40,"zig_target":"arm-linux-musleabi","cflags":["-march=armv5te","-mfloat-abi=soft"]},
 "aarch64":{"compiler":"aarch64-linux-gnu-gcc","machine":"AArch64","elf_machine":183,"zig_target":"aarch64-linux-musl"},
 "armv7":{"compiler":"arm-linux-gnueabihf-gcc","machine":"ARM","elf_machine":40,"zig_target":"arm-linux-musleabihf","cflags":["-march=armv7-a","-mfpu=vfpv3-d16","-mfloat-abi=hard"]},
 "riscv64":{"compiler":"riscv64-linux-gnu-gcc","machine":"RISC-V","elf_machine":243,"zig_target":"riscv64-linux-musl"},
 "ppc64le":{"compiler":"powerpc64le-linux-gnu-gcc","machine":"PowerPC64","elf_machine":21,"zig_target":"powerpc64le-linux-musl"},
 "s390x":{"compiler":"s390x-linux-gnu-gcc","machine":"IBM S/390","elf_machine":22,"zig_target":"s390x-linux-musl"}
}
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def zig_prefix(root):
 candidates=[]
 env_python=os.environ.get("CHIMERA_ZIG_PYTHON")
 if env_python: candidates.append(env_python)
 candidates.append(str(root/"build/toolchain-zig/bin/python"))
 candidates.append(sys.executable)
 zig=shutil.which("zig")
 if zig: return [zig]
 for python in candidates:
  if not python or (python!=sys.executable and not Path(python).is_file()): continue
  probe=subprocess.run([python,"-m","ziglang","version"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  if probe.returncode==0: return [python,"-m","ziglang"]
 return None
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--policy",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--require-all",action="store_true");a=p.parse_args()
 aliases=json.loads(a.policy.read_text())["native_build"]["multicall_aliases"]
 if not a.source.is_file():raise SystemExit(f"missing source: {a.source}")
 readelf=shutil.which("readelf")
 if not readelf:raise SystemExit("readelf is required")
 a.output.mkdir(parents=True,exist_ok=True);rows=[];failures=[]
 for target,spec in TARGETS.items():
  compiler=shutil.which(spec["compiler"]);backend="gnu-cross"
  if compiler:
   command=[compiler]
  else:
   zig=zig_prefix(ROOT)
   if not zig:
    row={"target":target,"compiler":spec["compiler"],"binary_status":"not-built","runtime_status":"not-tested","aliases":aliases,"reason":"cross compiler unavailable and pinned Zig toolchain not installed"}
    failures.append(target);rows.append(row);continue
   backend="zig-musl";command=[*zig,"cc","-target",spec["zig_target"]]
  row={"target":target,"compiler":spec["compiler"],"compiler_backend":backend,
       "compiler_command":" ".join(command),"zig_target":spec.get("zig_target"),
       "binary_status":"not-built","runtime_status":"not-tested","aliases":aliases}
  d=a.output/target;d.mkdir(parents=True,exist_ok=True);binary=d/"chimera-cmd"
  proc=subprocess.run([*command,*spec.get("cflags",[]),"-std=c11","-O2","-Wall","-Wextra","-Werror","-static",str(a.source),"-o",str(binary)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if proc.returncode:
   row["reason"]="compiler failed";row["compiler_stderr"]=proc.stderr[-4000:]
   print(f"[{target}] compiler failed:\\n{row['compiler_stderr']}",file=sys.stderr)
   failures.append(target);rows.append(row);continue
  hdr=subprocess.run([readelf,"-h",str(binary)],check=True,text=True,stdout=subprocess.PIPE).stdout
  machine=next((line.split(":",1)[1].strip() for line in hdr.splitlines() if line.strip().startswith("Machine:")),None)
  if not machine or spec["machine"].casefold() not in machine.casefold():row["reason"]=f"ELF machine mismatch: expected {spec['machine']}, got {machine}";failures.append(target);rows.append(row);continue
  for name in aliases:
   link=d/name
   if link.exists() or link.is_symlink():link.unlink()
   link.symlink_to("chimera-cmd")
  row.update({"compiler_backend":backend,"compiler_command":" ".join(command),"zig_target":spec.get("zig_target"),"binary_status":"cross-compiled-and-elf-machine-validated","elf_machine":machine,"elf_machine_id":spec["elf_machine"],"binary":str(binary.relative_to(a.output)),"sha256":sha256(binary),"runtime_status":"not-tested-cross-build-only"});rows.append(row)
 manifest={"schema":"CHM-LINUX-ABI-COMMAND-BUILD-1","policy":"Only compiled outputs with a verified ELF machine field are marked built. Cross-compilation is not native runtime acceptance.","native_command_count":len(aliases),"target_count":len(TARGETS),"targets":rows}
 (a.output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 for row in rows:
  if row["binary_status"]!="cross-compiled-and-elf-machine-validated":
   print(f"[{row['target']}] {row.get('reason','build failed')}: {row.get('compiler_stderr','')}",file=sys.stderr)
 print(json.dumps({"built":sum(r["binary_status"]=="cross-compiled-and-elf-machine-validated" for r in rows),"targets":len(rows),"failures":failures},sort_keys=True))
 return 1 if a.require_all and failures else 0
if __name__=="__main__":sys.exit(main())
