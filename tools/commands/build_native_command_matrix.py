#!/usr/bin/env python3
"""Cross-build the real Chimera native multicall command for supported Linux ABIs."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
TARGETS={
 "x86_64":{"compiler":"cc","machine":"Advanced Micro Devices X86-64","elf_machine":62},
 "i686":{"compiler":"i686-linux-gnu-gcc","machine":"Intel 80386","elf_machine":3},
 "armel":{"compiler":"arm-linux-gnueabi-gcc","machine":"ARM","elf_machine":40,"cflags":["-march=armv5te","-mfloat-abi=soft"]},
 "aarch64":{"compiler":"aarch64-linux-gnu-gcc-14","machine":"AArch64","elf_machine":183},
 "armv7":{"compiler":"arm-linux-gnueabihf-gcc","machine":"ARM","elf_machine":40,"cflags":["-march=armv7-a","-mfpu=vfpv3-d16","-mfloat-abi=hard"]},
 "riscv64":{"compiler":"riscv64-linux-gnu-gcc-14","machine":"RISC-V","elf_machine":243},
 "ppc64le":{"compiler":"powerpc64le-linux-gnu-gcc","machine":"PowerPC64","elf_machine":21},
 "s390x":{"compiler":"s390x-linux-gnu-gcc","machine":"IBM S/390","elf_machine":22}
}
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--policy",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--require-all",action="store_true");a=p.parse_args()
 aliases=json.loads(a.policy.read_text())["native_build"]["multicall_aliases"]
 if not a.source.is_file():raise SystemExit(f"missing source: {a.source}")
 readelf=shutil.which("readelf")
 if not readelf:raise SystemExit("readelf is required")
 a.output.mkdir(parents=True,exist_ok=True);rows=[];failures=[]
 for target,spec in TARGETS.items():
  compiler=shutil.which(spec["compiler"]);row={"target":target,"compiler":spec["compiler"],"binary_status":"not-built","runtime_status":"not-tested","aliases":aliases}
  if not compiler:row["reason"]="target compiler unavailable";failures.append(target);rows.append(row);continue
  d=a.output/target;d.mkdir(parents=True,exist_ok=True);binary=d/"chimera-cmd"
  proc=subprocess.run([compiler,*spec.get("cflags",[]),"-std=c11","-O2","-Wall","-Wextra","-Werror",str(a.source),"-o",str(binary)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if proc.returncode:row["reason"]="compiler failed";row["compiler_stderr"]=proc.stderr[-4000:];failures.append(target);rows.append(row);continue
  hdr=subprocess.run([readelf,"-h",str(binary)],check=True,text=True,stdout=subprocess.PIPE).stdout
  machine=next((line.split(":",1)[1].strip() for line in hdr.splitlines() if line.strip().startswith("Machine:")),None)
  if not machine or spec["machine"].casefold() not in machine.casefold():row["reason"]=f"ELF machine mismatch: expected {spec['machine']}, got {machine}";failures.append(target);rows.append(row);continue
  for name in aliases:
   link=d/name
   if link.exists() or link.is_symlink():link.unlink()
   link.symlink_to("chimera-cmd")
  row.update({"binary_status":"cross-compiled-and-elf-machine-validated","elf_machine":machine,"elf_machine_id":spec["elf_machine"],"binary":str(binary.relative_to(a.output)),"sha256":sha256(binary),"runtime_status":"not-tested-cross-build-only"});rows.append(row)
 manifest={"schema":"CHM-NATIVE-COMMAND-ISA-BUILD-1","policy":"Only compiled outputs with a verified ELF machine field are marked built. Cross-compilation is not native runtime acceptance.","native_command_count":len(aliases),"target_count":len(TARGETS),"targets":rows}
 (a.output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"built":sum(r["binary_status"]=="cross-compiled-and-elf-machine-validated" for r in rows),"targets":len(rows),"failures":failures},sort_keys=True))
 return 1 if a.require_all and failures else 0
if __name__=="__main__":sys.exit(main())
