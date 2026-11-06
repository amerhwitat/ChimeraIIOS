#!/usr/bin/env python3
"""Audit installed QEMU emulator binaries against the ISA family catalogue."""
from __future__ import annotations
import argparse,json
from pathlib import Path
MAP={"riscv":["qemu-riscv32","qemu-riscv64","qemu-riscv32-static","qemu-riscv64-static","qemu-system-riscv32","qemu-system-riscv64"],"aarch64":["qemu-aarch64","qemu-aarch64-static","qemu-system-aarch64"],"arm32":["qemu-arm","qemu-arm-static","qemu-system-arm"],"arm32-thumb":["qemu-arm","qemu-arm-static","qemu-system-arm"],"mips32":["qemu-mips","qemu-mipsel","qemu-mips-static","qemu-mipsel-static","qemu-system-mips","qemu-system-mipsel"],"power":["qemu-ppc","qemu-ppc64","qemu-ppc-static","qemu-ppc64-static","qemu-system-ppc","qemu-system-ppc64"],"sparc":["qemu-sparc","qemu-sparc64","qemu-sparc-static","qemu-sparc64-static","qemu-system-sparc","qemu-system-sparc64"],"systemz":["qemu-s390x","qemu-s390x-static","qemu-system-s390x"],"x86":["qemu-i386","qemu-x86_64","qemu-i386-static","qemu-x86_64-static","qemu-system-i386","qemu-system-x86_64"],"m68k":["qemu-m68k","qemu-m68k-static","qemu-system-m68k"],"vax":["vax","simh"]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--rootfs",type=Path,required=True);ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument("--output",type=Path);a=ap.parse_args();root=a.rootfs.resolve()
    cat=json.loads((a.repo/"isa/catalog.json").read_text()); rows=[]
    for fam in cat.get("families",[]):
        names=MAP.get(fam["id"],[]);found=[]
        for n in names:
            for d in ("usr/bin","usr/libexec","bin"):
                p=root/d/n
                if p.exists() and p.is_file() and p.stat().st_mode&0o111:found.append(str(p.relative_to(root)))
        rows.append({"family":fam["id"],"candidate_emulators":names,"installed_emulators":sorted(set(found)),"status":"emulator-binary-present-opcode-coverage-not-audited" if found else "no-emulator-provider-detected"})
    result={"schema":"CHM-ISA-EMULATOR-PROVIDER-AUDIT-1","catalogued_families":len(rows),"families":rows,"instruction_forms":len(cat.get("instructions",[])),"instruction_semantics":"not-audited-by-family-presence","policy":"An emulator executable does not prove every catalogued opcode or extension is implemented; unsupported families and instructions stay explicit."}
    out=a.output or root/"usr/share/chimera/catalogs/isa-emulator-provider-audit.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"families":len(rows),"emulator_providers":sum(x["status"].startswith("emulator-binary") for x in rows),"instruction_forms":result["instruction_forms"]},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
