#!/usr/bin/env python3
"""Generate truthful command/ISA coverage for the shipped BusyBox initramfs."""
from __future__ import annotations
import argparse, csv, json, re, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    ap.add_argument("--busybox",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    root=args.root.resolve()
    busybox=set(subprocess.check_output([str(args.busybox),"--list"],text=True).split())
    cmdfile=root/"system/commands/chimera-command-list.json"
    command_data=json.loads(cmdfile.read_text(encoding="utf-8"))
    linux=set(command_data.get("linux_bash",[]))
    registry=json.loads((root/"config/linux-command-registry.json").read_text(encoding="utf-8"))
    for group in registry.get("groups",{}).values():
        linux.update(group)
    builtins=set("""alias bg break builtin caller case cd command continue declare dirs echo eval exec exit export fc fg for function getopts hash help history if jobs let local logout mapfile popd printf pushd read readarray readonly return select set shift shopt source suspend test times trap type ulimit umask unalias unset until wait while""".split())
    rows=[]
    for name in sorted(linux,key=str.casefold):
        if not isinstance(name,str) or not name or "/" in name:
            continue
        if name in busybox:
            provider="busybox-applet"
            path="/bin/"+name
        elif name in builtins:
            provider="shell-builtin"
            path="/bin/sh"
        else:
            provider="catalogued-provider-required"
            path=None
        rows.append({"command":name,"provider":provider,"path":path})
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
            status="kernel-build-target-x86_64; instruction-by-instruction conformance must be tested"
        elif "aarch64" in key or "arm" in key:
            status="host-ISA-detection-only; no complete Koronos kernel target"
        elif "risc-v" in key or "riscv" in key:
            status="host-ISA-detection-only; no complete Koronos kernel target"
        else:
            status="catalogue-only; no executable Koronos backend declared"
        matrix.append({"architecture":arch,"instruction_forms":info["instruction_forms"],
                       "unique_mnemonics":len(info["mnemonics"]),"backend_status":status})
    online=root/"data/isa/online-isa-index.json"
    candidate_count=None
    if online.exists():
        try: candidate_count=json.loads(online.read_text(encoding="utf-8")).get("candidate_definition_count")
        except (OSError,json.JSONDecodeError): pass
    result={
      "schema":"CHIMERA-COMMAND-ISA-COVERAGE-1",
      "edition_targets":["ChimeraIIOS","OctavianOS"],
      "command_catalog_source":"system/commands/chimera-command-list.json + config/linux-command-registry.json",
      "busybox_binary":str(args.busybox),
      "busybox_applet_count":len(busybox),
      "linux_catalog_command_count":len(rows),
      "commands":rows,
      "command_summary":{
        "busybox_applet":sum(x["provider"]=="busybox-applet" for x in rows),
        "shell_builtin":sum(x["provider"]=="shell-builtin" for x in rows),
        "provider_required":sum(x["provider"]=="catalogued-provider-required" for x in rows)
      },
      "isa_source":"ISA.csv",
      "isa_architectures":matrix,
      "isa_candidate_definition_count":candidate_count,
      "limitations":[
        "A catalogue entry is not an executable binary; provider_required rows are not silently replaced by stubs.",
        "The ISA candidate index is discovery metadata, not a complete encoding or conformance database.",
        "The Koronos Makefile currently accepts only x86_64; AArch64/RISC-V host detection is not a bootable kernel port.",
        "Native instruction semantics, privileged operations, device services and per-architecture QEMU tests remain required."
      ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("command coverage:",result["command_summary"])
    print("ISA architectures:",len(matrix),"candidate definitions:",candidate_count)
if __name__=="__main__": main()
