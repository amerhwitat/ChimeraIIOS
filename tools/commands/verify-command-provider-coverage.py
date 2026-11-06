#!/usr/bin/env python3
"""Inventory command binaries actually present in a target rootfs.

Presence and ELF architecture are evidence only; they do not prove the command's
semantics, syscall compatibility, or Koronos runtime readiness.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, shutil, subprocess, sys
ROOTFS=pathlib.Path(sys.argv[1]).resolve()
CAPS=pathlib.Path(sys.argv[2]).resolve()
OUT=ROOTFS/"usr/share/chimera/commands/command-provider-coverage.json"
TARGET=sys.argv[3] if len(sys.argv)>3 else "x86_64"
MACHINES={"x86_64":"Advanced Micro Devices X86-64","amd64":"Advanced Micro Devices X86-64",
          "aarch64":"AArch64","arm64":"AArch64","i686":"Intel 80386","i386":"Intel 80386",
          "armv7":"ARM","riscv64":"RISC-V","ppc64le":"PowerPC64","s390x":"IBM S/390"}
EXPECTED=MACHINES.get(TARGET,TARGET)
SEARCH=( "usr/bin","bin","usr/sbin","sbin","usr/local/bin","usr/local/sbin" )
def executable(name):
    if not name or "/" in name or name in (".",".."): return None
    for base in SEARCH:
        p=ROOTFS/base/name
        if p.is_file() and os.access(p,os.X_OK): return p
    return None
def runtime_present(provider):
    key=(provider or "").casefold()
    names=[]
    if "windows" in key: names=["cmd.exe","wine","wine64","pwsh","powershell"]
    elif "powershell" in key: names=["pwsh","powershell"]
    elif "dos" in key: names=["dosbox","dosbox-x"]
    elif "darwin" in key or "macos" in key: names=["darling"]
    elif "wasm" in key or "webassembly" in key: names=["wasmtime","wasmer"]
    elif "qemu" in key: names=["qemu-aarch64","qemu-arm","qemu-i386","qemu-riscv64","qemu-ppc64le"]
    return next((executable(n) for n in names if executable(n)),None)
caps=json.loads(CAPS.read_text(encoding="utf-8"))
rows=[]
for item in caps.get("commands",[]):
    name=str(item.get("name","")).strip()
    mode=item.get("mode","")
    provider=item.get("provider","")
    binary=None
    if mode=="native":
        binary=executable("chimera-cmd")
        status="native-multicall-binary-present" if binary else "native-implementation-not-staged"
    elif mode=="shell-builtin":
        binary=executable("bash") or executable("dash") or executable("sh")
        status="shell-runtime-present-builtin-not-separate-binary" if binary else "shell-runtime-missing"
    else:
        binary=executable(name)
        if binary: status="provider-binary-present-runtime-unverified"
        else:
            rt=runtime_present(provider)
            if rt: binary=rt; status="compatibility-runtime-present-command-unverified"
            else: status="provider-binary-and-runtime-missing"
    row={"name":name,"mode":mode,"provider":provider,"platforms":item.get("platforms",[]),"status":status}
    if binary:
        rel="/"+str(binary.relative_to(ROOTFS))
        data=binary.read_bytes()
        row.update(path=rel,sha256=hashlib.sha256(data).hexdigest())
        if data[:4]==b"\x7fELF":
            readelf=shutil.which("readelf")
            if readelf:
                proc=subprocess.run([readelf,"-h",str(binary)],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                machine=next((x.split(":",1)[1].strip() for x in proc.stdout.splitlines() if x.strip().startswith("Machine:")),None)
                row["elf_machine"]=machine
                if machine and EXPECTED not in machine and machine not in EXPECTED:
                    row["status"]="wrong-architecture-provider-binary"
    rows.append(row)
counts={}
for row in rows: counts[row["status"]]=counts.get(row["status"],0)+1
result={"schema":"CHIMERA-COMMAND-PROVIDER-COVERAGE-1","target_architecture":TARGET,
        "catalog_count":len(rows),"counts":counts,
        "policy":"Binary presence/hash/ELF architecture are not semantic or Koronos ABI validation.",
        "commands":rows}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("[COMMAND-PROVIDERS] catalogued=%d counts=%s"%(len(rows),json.dumps(counts,sort_keys=True)))
