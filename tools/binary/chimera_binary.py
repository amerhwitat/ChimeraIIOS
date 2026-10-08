#!/usr/bin/env python3
"""Passive binary identification and NCB1 reference-format validation."""
import argparse, json, struct
from pathlib import Path
NCB_MAGIC=b"NCB1"
NCB_HEADER=struct.Struct("<4sHHIHHIQQQQQQQ")
NCB_SECTION=struct.Struct("<16sIQQQQ")
MAX_SECTIONS=128
MACHINES={3:"x86",40:"ARM",62:"x86-64",183:"AArch64",243:"RISC-V"}
PE_MACHINES={0x14c:"x86",0x8664:"x86-64",0x1c0:"ARM",0x1c4:"ARM Thumb-2",0xaa64:"AArch64",0x5064:"RISC-V 64",0x5032:"RISC-V 32"}
def identify(data, filename=""):
    def result(fmt, arch="unknown", kind="executable", notes=None):
        return {"filename":Path(filename).name,"format":fmt,"architecture":arch,"kind":kind,"executable_compatibility":"unknown-until-ABI-and-runtime-check","notes":notes or []}
    if data.startswith(NCB_MAGIC):
        if len(data)<NCB_HEADER.size:return result("Chimera NCB1",notes=["truncated native header"])
        try:
            _,ver,hs,flags,isa,word,count,entry,sto,fs,stack,heap,base,res=NCB_HEADER.unpack_from(data)
            if ver!=1 or hs<NCB_HEADER.size or hs>len(data) or count>MAX_SECTIONS or fs!=len(data) or word<8 or word>1048576 or word%8 or sto<hs or sto+count*NCB_SECTION.size>len(data):
                return result("Chimera NCB1",notes=["invalid or unsupported NCB1 header fields"])
            return result("Chimera NCB1",f"Chimera-ISA-{isa}/N-bit-{word}",notes=[f"version={ver}",f"sections={count}",f"entry_offset=0x{entry:x}",f"stack_bytes={stack}",f"heap_limit_bytes={heap}","passive format recognition only"])
        except struct.error:return result("Chimera NCB1",notes=["malformed native header"])
    if data.startswith(b"\x7fELF"):
        if len(data)<20:return result("ELF",notes=["truncated ELF header"])
        bits={1:32,2:64}.get(data[4],"unknown"); endian={1:"little",2:"big"}.get(data[5])
        if endian:return result(f"ELF{bits}",MACHINES.get(int.from_bytes(data[18:20],endian),f"EM_{int.from_bytes(data[18:20],endian)}"),notes=["machine/ABI/runtime compatibility still required"])
        return result("ELF",notes=["invalid ELF class or byte order"])
    if data.startswith(b"MZ"):
        if len(data)>=0x40:
            off=int.from_bytes(data[0x3c:0x40],"little")
            if off+6<=len(data) and data[off:off+4]==b"PE\0\0":
                m=int.from_bytes(data[off+4:off+6],"little")
                return result("PE/COFF",PE_MACHINES.get(m,f"machine-0x{m:04x}"),notes=["Windows ABI layer required"])
        return result("DOS MZ/PE candidate",notes=["MZ signature only; PE not verified"])
    if data.startswith(b"\0asm\x01\0\0\0"):return result("WebAssembly","wasm32","module",["requires compatible runtime"])
    if data.startswith(b"\xca\xfe\xba\xbe"):return result("Java class or Mach-O universal","unknown","container",["ambiguous magic; inspect structure"])
    if data.startswith(b"PK\x03\x04"):return result("ZIP container","unknown","container",["may be JAR/APK/package/ordinary ZIP"])
    if data[:4] in (b"\xfe\xed\xfa\xce",b"\xce\xfa\xed\xfe",b"\xfe\xed\xfa\xcf",b"\xcf\xfa\xed\xfe"):return result("Mach-O","unknown",notes=["CPU type needs full header validation"])
    if data.startswith(b"#!"):return result("script","interpreter-dependent","script",["requires installed interpreter and policy"])
    if data.startswith(b"!<arch>\n"):return result("ar archive","unknown","container",["object archive is not a directly executable image"])
    return result("unknown/data","unknown","data",["never execute based on extension alone"])
def validate_ncb(data):
    r=identify(data)
    if r["format"]!="Chimera NCB1" or any(x in " ".join(r["notes"]) for x in ("invalid","truncated","malformed")):raise ValueError("invalid NCB1 header")
    _,ver,hs,flags,isa,word,count,entry,sto,fs,stack,heap,base,res=NCB_HEADER.unpack_from(data)
    sections=[]
    for i in range(count):
        name,fl,off,filesz,memsz,align=NCB_SECTION.unpack_from(data,sto+i*NCB_SECTION.size)
        if filesz>memsz or off>len(data) or filesz>len(data)-off:raise ValueError(f"section {i} range invalid")
        if align and (align&(align-1) or off%align):raise ValueError(f"section {i} alignment invalid")
        sections.append({"name":name.split(b"\0",1)[0].decode("ascii","replace"),"flags":fl,"file_offset":off,"file_size":filesz,"memory_size":memsz,"alignment":align})
    if entry and not any(s["flags"]&1 and s["file_offset"]<=entry<s["file_offset"]+s["file_size"] for s in sections):raise ValueError("entry must be in a file-backed executable section")
    return {"format":"Chimera NCB1","version":ver,"isa_id":isa,"word_bits":word,"entry_offset":entry,"file_size":fs,"stack_bytes":stack,"heap_limit_bytes":heap,"image_base":base,"sections":sections}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("file");p.add_argument("--json",action="store_true");a=p.parse_args();path=Path(a.file)
    if not path.is_file():p.error("input must be a regular file")
    if path.stat().st_size>1<<34:p.error("file exceeds safe inspection limit")
    data=path.read_bytes();r=identify(data,str(path))
    if r["format"]=="Chimera NCB1":
        try:r["validation"]=validate_ncb(data)
        except ValueError as e:r["validation_error"]=str(e)
    print(json.dumps(r,indent=2) if a.json else f'{r["format"]}: {r["architecture"]}')
    return 0 if r["format"]!="unknown/data" else 2
if __name__=="__main__":raise SystemExit(main())
