#!/usr/bin/env python3
import struct,sys
def validate(path):
    with open(path,"rb") as f: data=f.read(64)
    if len(data)<64 or data[:4]!=b"\x7fELF" or data[4]!=2 or data[5]!=1:
        raise SystemExit("invalid ELF64 header: "+path)
    machine=struct.unpack_from("<H",data,18)[0]
    entry=struct.unpack_from("<Q",data,24)[0]
    print(f"{path}: ELF64 machine={machine} entry=0x{entry:x}")
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: validate_elf.py <file>")
    validate(sys.argv[1])
