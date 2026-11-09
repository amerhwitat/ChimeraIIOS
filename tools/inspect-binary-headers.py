#!/usr/bin/env python3
"""Identify executable/container formats and key CPU/OS header fields without executing them."""
import argparse
import json
import struct
from pathlib import Path

ELF_MACHINES = {
    3:"i386", 8:"MIPS", 20:"PowerPC", 21:"PowerPC64", 22:"s390",
    40:"ARM", 42:"SuperH", 43:"SPARCv9", 50:"IA-64", 62:"x86_64",
    183:"AArch64", 243:"RISC-V", 258:"LoongArch",
}
PE_MACHINES = {
    0x014C:"i386", 0x8664:"x86_64", 0x01C0:"ARM", 0x01C4:"ARMv7",
    0xAA64:"AArch64", 0x0200:"IA-64", 0x5032:"RISC-V32",
    0x5064:"RISC-V64", 0x5128:"RISC-V128",
}
MACH_CPUS = {
    7:"i386", 0x01000007:"x86_64", 12:"ARM", 0x0100000C:"AArch64",
    18:"PowerPC", 0x01000012:"PowerPC64",
}
ELF_TYPES={1:"relocatable",2:"executable",3:"shared-object",4:"core"}
PE_SUBSYSTEMS={1:"native",2:"windows-gui",3:"windows-console",7:"posix-console",10:"efi-application",11:"efi-boot-service-driver",12:"efi-runtime-driver",14:"xbox"}
def result(fmt, os_name, arch="unknown", bits=None, endian=None, **extra):
    return {"format":fmt,"os":os_name,"architecture":arch,"bits":bits,"endianness":endian,**extra}

def inspect(data):
    if data.startswith(b"\x7fELF") and len(data)>=20:
        cls,enc,abi,abi_version=data[4],data[5],data[7],data[8]
        endian="little" if enc==1 else "big" if enc==2 else "unknown"
        order="<" if enc==1 else ">" if enc==2 else "="
        machine=struct.unpack(order+"H",data[18:20])[0]
        file_type=struct.unpack(order+"H",data[16:18])[0]
        entry=None
        if cls==2 and len(data)>=32: entry=struct.unpack(order+"Q",data[24:32])[0]
        elif cls==1 and len(data)>=28: entry=struct.unpack(order+"I",data[24:28])[0]
        return result("ELF","Unix/Linux",ELF_MACHINES.get(machine,f"EM_{machine}"),
                      32 if cls==1 else 64 if cls==2 else None,endian,
                      os_abi=abi,abi_version=abi_version,elf_class=cls,
                      file_type=ELF_TYPES.get(file_type,f"ET_{file_type}"),
                      entry_point=f"0x{entry:x}" if entry is not None else None)
    if data.startswith(b"MZ") and len(data)>=64:
        pe_offset=struct.unpack("<I",data[0x3C:0x40])[0]
        if pe_offset+24<=len(data) and data[pe_offset:pe_offset+4]==b"PE\0\0":
            coff=pe_offset+4
            machine,sections=struct.unpack("<HH",data[coff:coff+4])
            optional_size=struct.unpack("<H",data[coff+16:coff+18])[0]
            characteristics=struct.unpack("<H",data[coff+18:coff+20])[0]
            opt=coff+20
            magic=struct.unpack("<H",data[opt:opt+2])[0] if optional_size>=2 and opt+2<=len(data) else 0
            bits=64 if magic==0x20B else 32 if magic==0x10B else None
            entry=struct.unpack("<I",data[opt+16:opt+20])[0] if optional_size>=20 and opt+20<=len(data) else None
            subsystem=struct.unpack("<H",data[opt+68:opt+70])[0] if optional_size>=70 and opt+70<=len(data) else None
            return result("PE/COFF","Windows",PE_MACHINES.get(machine,f"PE_MACHINE_{machine:#x}"),
                          bits,"little",machine=f"{machine:#06x}",section_count=sections,
                          optional_header="PE32+" if magic==0x20B else "PE32" if magic==0x10B else "unknown",
                          entry_rva=f"0x{entry:x}" if entry is not None else None,
                          subsystem=PE_SUBSYSTEMS.get(subsystem,f"subsystem-{subsystem}") if subsystem is not None else None,
                          characteristics=f"0x{characteristics:04x}")
        return result("DOS MZ","DOS","x86",16,"little",note="MZ header; not a PE image")
    if len(data)>=8:
        magic=data[:4]
        mach={b"\xfe\xed\xfa\xce":("big",32),b"\xce\xfa\xed\xfe":("little",32),
              b"\xfe\xed\xfa\xcf":("big",64),b"\xcf\xfa\xed\xfe":("little",64)}
        if magic in mach:
            endian,bits=mach[magic];order=">" if endian=="big" else "<"
            cpu,subtype,filetype,ncmds=struct.unpack(order+"IIII",data[4:20])
            return result("Mach-O","macOS/Darwin",MACH_CPUS.get(cpu,f"CPU_{cpu:#x}"),
                          bits,endian,cpu_type=f"{cpu:#x}",cpu_subtype=f"{subtype:#x}",
                          file_type=filetype,load_commands=ncmds)
        fat={b"\xca\xfe\xba\xbe":">",b"\xbe\xba\xfe\xca":"<"}
        if magic in fat:
            order=fat[magic];count=struct.unpack(order+"I",data[4:8])[0]
            archs=[];offset=8
            if count<=64:
                for _ in range(count):
                    if offset+20>len(data): break
                    cpu,subtype,_,_,_=struct.unpack(order+"IIIII",data[offset:offset+20])
                    archs.append(MACH_CPUS.get(cpu,f"CPU_{cpu:#x}"));offset+=20
            return result("Mach-O Universal","macOS/Darwin","multiple",None,
                          "big" if order==">" else "little",architecture_count=count,
                          architectures=archs)
        if magic==bytes.fromhex("cafebabe") and len(data)>=8:
            minor,major=struct.unpack(">HH",data[4:8])
            if 45<=major<=1000:
                return result("Java Class","JVM","bytecode",None,"big",
                              major_version=major,minor_version=minor)
    if data.startswith(b"\0asm") and len(data)>=8:
        version=struct.unpack("<I",data[4:8])[0]
        return result("WebAssembly","WASI/Web","wasm",32,"little",version=version)
    return result("unknown","unknown",note="No recognized executable header")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files",nargs="+",type=Path)
    parser.add_argument("--json",action="store_true",help="emit JSON")
    args=parser.parse_args()
    reports=[];failed=False
    for path in args.files:
        try: reports.append({"path":str(path),**inspect(path.read_bytes()[:4096])})
        except OSError as exc:
            failed=True;reports.append({"path":str(path),"error":str(exc)})
    if args.json: print(json.dumps(reports,indent=2))
    else:
        for item in reports:
            if "error" in item: print(f"{item['path']}: ERROR: {item['error']}")
            else: print(f"{item['path']}: {item['format']} | {item['os']} | {item['architecture']} | "
                         f"{item['bits'] or '?'}-bit | {item['endianness'] or 'unknown'} endian")
    return 1 if failed else 0
if __name__=="__main__": raise SystemExit(main())
