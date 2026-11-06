#!/usr/bin/env python3
"""Audit real terminal/shell executables staged in a target root filesystem."""
from __future__ import annotations
import argparse,hashlib,json,struct,subprocess,shutil
from pathlib import Path
def elf_machine(p):
    try:
        with p.open("rb") as f:
            h=f.read(20)
        if h[:4]!=b"\x7fELF": return None
        endian="<" if h[5]==1 else ">"
        return struct.unpack(endian+"H",h[18:20])[0]
    except (OSError,struct.error): return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rootfs",type=Path,required=True); ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[2]); ap.add_argument("--output",type=Path); a=ap.parse_args()
    root=a.rootfs.resolve()
    terminal=json.loads((a.repo/"aurora/terminals/registry.json").read_text())
    shells=json.loads((a.repo/"aurora/shells/registry.json").read_text())
    rows=[]
    for group,entries in (("terminal",terminal["entries"]),("shell",shells["entries"])):
        for item in entries:
            binary=item["binary"]; candidates=[root/"usr/bin"/binary,root/"bin"/binary,root/"usr/local/bin"/binary,root/"usr/sbin"/binary,root/"usr/local/sbin"/binary]
            found=next((p for p in candidates if p.exists() and p.is_file()),None)
            resolved=None; machine=None; status="provider-missing"
            if found:
                try:
                    resolved=found.resolve(strict=True)
                    resolved.relative_to(root)
                    machine=elf_machine(resolved)
                    status="verified-elf-provider" if machine is not None and resolved.stat().st_mode & 0o111 else "present-but-not-verified-elf"
                except (OSError,ValueError): status="unsafe-or-broken-path"
            rows.append({"id":item["id"],"name":item["name"],"kind":group,"binary":binary,"source":item.get("source"),"status":status,"elf_machine":machine,"sha256":hashlib.sha256(resolved.read_bytes()).hexdigest() if resolved else None,"path":str(found.relative_to(root)) if found else None})
    result={"schema":"CHM-AURORA-TERMINAL-SHELL-AUDIT-1","architecture":"derived-from-ELF-machine","summary":{},"entries":rows,"policy":"Registry entries are not treated as installed until a real executable ELF provider is found inside the target rootfs."}
    for kind in ("terminal","shell"):
        subset=[x for x in rows if x["kind"]==kind]
        result["summary"][kind]={"catalogued":len(subset),"verified_elf":sum(x["status"]=="verified-elf-provider" for x in subset),"missing":sum(x["status"]=="provider-missing" for x in subset),"other":sum(x["status"] not in ("verified-elf-provider","provider-missing") for x in subset)}
    out=a.output or root/"usr/share/chimera/aurora/terminal-shell-provider-audit.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result["summary"],sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
