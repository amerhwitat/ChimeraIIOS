#!/usr/bin/env python3
"""Generate truthful command/ISA coverage for shipped OS and initramfs runtimes."""
from __future__ import annotations
import argparse, csv, json, subprocess, stat
from pathlib import Path

PLATFORMS={
    "linux_bash":"linux-bash",
    "macos_core":"macos",
    "windows_cmd_core":"windows-cmd",
    "powershell_core":"powershell",
    "vbscript_core":"vbscript",
    "sql_server_core":"sql-server",
    "native_chimera":"chimera-native",
}
NATIVE_IMPLEMENTED={"pwd","echo","ls","cp","mv","touch","mkdir","rm","cat","clear","whoami","hostname","date","true","false"}
SHELL_BUILTINS=set("""alias bg break builtin caller case cd command continue declare dirs echo eval exec exit export fc fg for function getopts hash help history if jobs let local logout mapfile popd printf pushd read readarray readonly return select set shift shopt source suspend test times trap type ulimit umask unalias unset until wait while""".split())

def rootfs_executable(rootfs: Path | None, name: str):
    if rootfs is None:
        return None
    for directory in ("usr/local/bin", "usr/local/sbin", "usr/bin", "usr/sbin", "bin", "sbin"):
        candidate=rootfs/directory/name
        try:
            if candidate.is_file() and (candidate.stat().st_mode & (stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)):
                return "/" + str(candidate.relative_to(rootfs))
        except OSError:
            continue
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    ap.add_argument("--busybox",type=Path,required=True)
    ap.add_argument("--native-matrix",type=Path)
    ap.add_argument("--rootfs",type=Path,help="Target root filesystem to inspect for real executable providers")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    root=args.root.resolve()
    target_rootfs=args.rootfs.resolve() if args.rootfs else None
    busybox=set(subprocess.check_output([str(args.busybox),"--list"],text=True).split())
    catalog=json.loads((root/"system/commands/chimera-command-list.json").read_text(encoding="utf-8"))
    rows={}
    for field,platform in PLATFORMS.items():
        for raw in catalog.get(field,[]):
            name=raw.get("name") if isinstance(raw,dict) else raw
            if not isinstance(name,str) or not name.strip() or "/" in name: continue
            name=name.strip()
            if not any(char.isalnum() or char == "_" for char in name): continue
            row=rows.setdefault(name.casefold(),{"command":name,"platforms":[]})
            if platform not in row["platforms"]: row["platforms"].append(platform)
    registry=json.loads((root/"config/linux-command-registry.json").read_text(encoding="utf-8"))
    for group,names in registry.get("groups",{}).items():
        for name in names:
            row=rows.setdefault(str(name).casefold(),{"command":str(name),"platforms":[]})
            if "linux-bash" not in row["platforms"]: row["platforms"].append("linux-bash")
    for row in rows.values():
        name=row["command"]
        if "linux-bash" in row["platforms"]:
            target_path=rootfs_executable(target_rootfs,name)
            if name in busybox and target_path:
                candidate=target_rootfs/target_path.lstrip("/")
                busybox_path=target_rootfs/"bin/busybox"
                try:
                    is_busybox_link=candidate.is_symlink() and candidate.resolve()==busybox_path.resolve()
                except OSError:
                    is_busybox_link=False
                if is_busybox_link:
                    row.update(provider="busybox-applet",path=target_path)
                else:
                    row.update(provider="target-rootfs-executable",path=target_path)
            elif name in busybox:
                row.update(provider="busybox-applet-dispatch-only",path="/bin/busybox "+name)
            elif name in SHELL_BUILTINS:
                row.update(provider="shell-builtin",path="/bin/sh")
            elif target_path:
                row.update(provider="target-rootfs-executable",path=target_path)
            else:
                row.update(provider="catalogued-provider-required",path=None)
        elif "chimera-native" in row["platforms"]:
            target_path=rootfs_executable(target_rootfs,name)
            if name.casefold() in NATIVE_IMPLEMENTED:
                row.update(provider="native-command-source-present",path=None)
            elif target_path:
                row.update(provider="hosted-linux-rootfs-executable",path=target_path,
                           native_koronos_status="not-implemented-by-linux-provider")
            else:
                row.update(provider="native-candidate-not-yet-implemented",path=None,
                           native_koronos_status="not-implemented")
        else:
            row.update(provider="compatibility-provider-required",path=None)
        row["platforms"].sort()
    matrix_path=args.native_matrix or (root/"build/native-command-isa/manifest.json")
    native_matrix=None
    native_targets={}
    if matrix_path.exists():
        try:
            native_matrix=json.loads(matrix_path.read_text(encoding="utf-8"))
            native_targets={row.get("target"):row for row in native_matrix.get("targets",[])}
        except (OSError,json.JSONDecodeError):
            native_matrix=None
            native_targets={}
    for row in rows.values():
        if "chimera-native" in row["platforms"]:
            built=[arch for arch,entry in native_targets.items() if entry.get("binary_status")=="cross-compiled-and-elf-machine-validated" and row["command"] in entry.get("aliases",[])]
            row["native_binary_targets"]=sorted(built)
            row["native_runtime_status"]=native_targets.get(built[0],{}).get("runtime_status","cross-build-only") if built else "not-built-or-not-verified"
            row["native_koronos_status"]="not-tested-koronos-abi"
            if "linux-bash" not in row["platforms"]:
                row["provider"]="linux-abi-multicall-crossbuilt" if built else row["provider"]
                row["path"]=None

    csv_path=root/"ISA.csv"
    isa={}
    if csv_path.exists():
        with csv_path.open(newline="",encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                arch=(row.get("architecture") or "").strip()
                if not arch: continue
                info=isa.setdefault(arch,{"instruction_forms":0,"mnemonics":set()})
                info["instruction_forms"]+=1
                if row.get("mnemonic"): info["mnemonics"].add(row["mnemonic"].strip())
    matrix=[]
    for arch,info in sorted(isa.items()):
        key=arch.casefold()
        if "x86" in key:
            status="Koronos x86_64 kernel build target; instruction-by-instruction conformance remains partial"
        elif "aarch64" in key or "arm" in key:
            status="host ISA detection only; no complete Koronos kernel target"
        elif "risc-v" in key or "riscv" in key:
            status="host ISA detection only; no complete Koronos kernel target"
        else:
            status="catalogue-only; no executable Koronos backend declared"
        target_key={"x86-64":"x86_64","x86_64":"x86_64","i686":"i686","x86":"i686","aarch64":"aarch64","armv7":"armv7","arm":"armv7","riscv64":"riscv64","ppc64le":"ppc64le","powerpc64le":"ppc64le","s390x":"s390x"}.get(key)
        cmd_row=native_targets.get(target_key,{}) if target_key else {}
        command_status=cmd_row.get("binary_status","not-built")
        matrix.append({"architecture":arch,"instruction_forms":info["instruction_forms"],
                       "unique_mnemonics":len(info["mnemonics"]),"backend_status":status,
                       "native_command_binary_status":command_status,
                       "native_command_runtime_status":cmd_row.get("runtime_status","not-tested")})
    online=root/"data/isa/online-isa-index.json"
    candidate_count=None
    if online.exists():
        try: candidate_count=json.loads(online.read_text(encoding="utf-8")).get("candidate_definition_count")
        except (OSError,json.JSONDecodeError): pass
    command_rows=sorted(rows.values(),key=lambda x:x["command"].casefold())
    counts={}
    for row in command_rows: counts[row["provider"]]=counts.get(row["provider"],0)+1
    result={
      "schema":"CHIMERA-COMMAND-ISA-COVERAGE-2",
      "edition_targets":["ChimeraIIOS","OctavianOS"],
      "command_catalog_source":"system/commands/chimera-command-list.json + config/linux-command-registry.json",
      "busybox_binary":str(args.busybox),
      "target_rootfs":str(target_rootfs) if target_rootfs else None,
      "provider_scope":"A target-rootfs executable is verified for the specified hosted Linux image only; it does not prove Koronos-native ABI support.",
      "busybox_applet_count":len(busybox),
      "catalogued_command_count":len(command_rows),
      "commands":command_rows,
      "command_summary":counts,
      "linux_abi_command_build_matrix":native_matrix or {"status":"not-run","targets":[]},
      "isa_source":"ISA.csv",
      "isa_architectures":matrix,
      "isa_candidate_definition_count":candidate_count,
      "limitations":[
        "Catalogue entries are not automatically executable binaries; provider-required and candidate rows are not replaced by fake stubs.",
        "The ISA candidate index is discovery metadata, not a complete encoding or conformance database.",
        "The Koronos Makefile currently accepts only x86_64; the seven Linux command ABIs are cross-build candidates, not bootable Koronos ports.",
        "Native instruction semantics, privileged operations, device services and per-architecture QEMU tests remain required."
      ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("command coverage:",counts)
    print("ISA architectures:",len(matrix),"candidate definitions:",candidate_count)
if __name__=="__main__": main()
