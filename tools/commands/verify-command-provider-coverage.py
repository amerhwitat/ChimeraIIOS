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
          "armel":"ARM","armv7":"ARM","riscv64":"RISC-V","ppc64le":"PowerPC64","ppc64el":"PowerPC64","s390x":"IBM S/390"}
EXPECTED=MACHINES.get(TARGET,TARGET)
ABI_TARGET={"amd64":"x86_64","i386":"i686","armel":"armel","armhf":"armv7","arm64":"aarch64","ppc64el":"ppc64le"}.get(TARGET,TARGET)
MATRIX_PATH=ROOTFS/"usr/share/chimera/catalogs/linux-abi-command-matrix.json"
try:
    matrix=json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
except (OSError,json.JSONDecodeError):
    matrix={}
abi_row=next((x for x in matrix.get("targets",[]) if x.get("target")==ABI_TARGET),{})
abi_aliases=set(abi_row.get("aliases",[])) if abi_row.get("binary_status")=="cross-compiled-and-elf-machine-validated" else set()
SEARCH=( "usr/bin","bin","usr/sbin","sbin","usr/local/bin","usr/local/sbin" )
def executable(name):
    if not name or "/" in name or name in (".",".."): return None
    for base in SEARCH:
        p=ROOTFS/base/name
        if p.is_file() and os.access(p,os.X_OK): return p
    return None
def linux_abi_alias(name):
    if name not in abi_aliases: return None
    candidate=ROOTFS/"usr/lib/chimera/commands/linux-abi"/ABI_TARGET/name
    return candidate if candidate.is_file() and os.access(candidate,os.X_OK) else None

def runtime_present(provider):
    key=(provider or "").casefold()
    names=[]
    if "windows" in key: names=["cmd.exe","wine","wine64","pwsh","powershell"]
    elif "powershell" in key: names=["pwsh","powershell"]
    elif "dos" in key: names=["dosbox","dosbox-x"]
    elif "darwin" in key or "macos" in key: names=["darling"]
    elif "wasm" in key or "webassembly" in key: names=["wasmtime","wasmer"]
    elif "qemu" in key: names=["qemu-aarch64","qemu-arm","qemu-i386","qemu-riscv64","qemu-ppc64le"]
    elif "busybox" in key: names=["busybox"]
    return next((executable(n) for n in names if executable(n)),None)
caps=json.loads(CAPS.read_text(encoding="utf-8"))
rows=[]
_digest_cache={}
_elf_cache={}
for item in caps.get("commands",[]):
    name=str(item.get("name","")).strip()
    mode=item.get("mode","")
    provider=item.get("provider","")
    binary=None
    if mode=="language-feature":
        status="not-a-standalone-executable"
    elif mode=="native":
        script_rel=item.get("provider_binary")
        if script_rel:
            candidate=ROOTFS/str(script_rel).lstrip("/")
            binary=candidate if candidate.is_file() and os.access(candidate,os.X_OK) else None
            status="native-script-provider-present-not-koronos-native" if binary else "native-script-provider-not-staged"
        else:
            binary=linux_abi_alias(name)
            if binary:
                status="linux-abi-multicall-alias-present-not-koronos-native"
            else:
                binary=executable(name)
                status="external-provider-binary-present-native-implementation-not-staged" if binary else "native-implementation-not-staged"
    elif mode=="shell-builtin":
        binary=executable("bash") or executable("dash") or executable("sh")
        status="shell-runtime-present-builtin-not-separate-binary" if binary else "shell-runtime-missing"
    else:
        binary=executable(name)
        if binary: status="provider-binary-present-runtime-unverified"
        else:
            rt=runtime_present(provider)
            if rt and "busybox" in str(provider).casefold():
                probe=subprocess.run([str(rt),"--list"],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                if name in set(probe.stdout.split()): binary=rt; status="provider-multicall-applet-present"
                else: status="provider-multicall-applet-missing"
            elif rt: binary=rt; status="compatibility-runtime-present-command-unverified"
            else: status="provider-binary-and-runtime-missing"
    row={"name":name,"mode":mode,"entry_kind":item.get("entry_kind","executable-command"),"provider":provider,"platforms":item.get("platforms",[]),"status":status}
    if mode=="native":
        row["linux_abi_target"]=ABI_TARGET
        row["linux_abi_runtime_status"]=abi_row.get("runtime_status","not-tested") if binary and status.startswith("linux-abi-") else "not-applicable"
        if item.get("provider_binary"): row["native_script_provider_path"]=item["provider_binary"]
        row["koronos_runtime_status"]="not-tested-koronos-abi"
    if binary:
        rel="/"+str(binary.relative_to(ROOTFS))
        resolved=binary.resolve()
        digest=_digest_cache.get(resolved)
        if digest is None:
            data=binary.read_bytes()
            digest=hashlib.sha256(data).hexdigest()
            _digest_cache[resolved]=digest
        else:
            data=None
        row.update(path=rel,sha256=digest)
        elf_info=_elf_cache.get(resolved)
        if elf_info is None:
            if data is not None:
                is_elf=data[:4]==b"\x7fELF"
            else:
                with binary.open("rb") as stream: is_elf=stream.read(4)==b"\x7fELF"
            machine=None
            readelf=shutil.which("readelf")
            if is_elf and readelf:
                proc=subprocess.run([readelf,"-h",str(binary)],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                machine=next((x.split(":",1)[1].strip() for x in proc.stdout.splitlines() if x.strip().startswith("Machine:")),None)
            elf_info=(is_elf,machine)
            _elf_cache[resolved]=elf_info
        is_elf,machine=elf_info
        if is_elf and machine:
            row["elf_machine"]=machine
            if EXPECTED not in machine and machine not in EXPECTED:
                row["status"]="wrong-architecture-provider-binary"
    rows.append(row)
counts={}
for row in rows: counts[row["status"]]=counts.get(row["status"],0)+1
result={"schema":"CHIMERA-COMMAND-PROVIDER-COVERAGE-2","target_architecture":TARGET,
        "catalog_count":len(rows),"counts":counts,
        "linux_abi_matrix_target":ABI_TARGET,"linux_abi_matrix_status":abi_row.get("binary_status","not-built"),
        "linux_abi_alias_count":len(abi_aliases),
        "policy":"Binary presence/hash/ELF architecture are not semantic or Koronos ABI validation.",
        "commands":rows}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("[COMMAND-PROVIDERS] catalogued=%d counts=%s"%(len(rows),json.dumps(counts,sort_keys=True)))
