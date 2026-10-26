#!/usr/bin/env python3
"""Fail-closed PE/COFF EFI application structural validator; not a boot test."""
import argparse, struct, sys
from pathlib import Path
PROFILES = {"x86": (0x014c, 0x10b), "x86_64": (0x8664, 0x20b),
 "aarch64": (0xaa64, 0x20b), "riscv32": (0x5032, 0x10b),
 "riscv64": (0x5064, 0x20b), "loongarch64": (0x6264, 0x20b)}
class PEValidationError(ValueError): pass
def u16(d,o):
 if o < 0 or o+2 > len(d): raise PEValidationError("truncated 16-bit field")
 return struct.unpack_from("<H",d,o)[0]
def u32(d,o):
 if o < 0 or o+4 > len(d): raise PEValidationError("truncated 32-bit field")
 return struct.unpack_from("<I",d,o)[0]
def validate_pe(d,target):
 if target not in PROFILES: raise PEValidationError("unsupported target profile")
 if len(d)<0x40 or d[:2]!=b"MZ": raise PEValidationError("missing/truncated DOS header")
 pe=u32(d,0x3c)
 if pe>len(d) or pe+24>len(d) or d[pe:pe+4]!=b"PE\0\0": raise PEValidationError("invalid or truncated PE signature/header")
 c=pe+4; machine=u16(d,c); n=u16(d,c+2); osz=u16(d,c+16)
 if machine!=PROFILES[target][0]: raise PEValidationError("COFF machine does not match target")
 if n==0: raise PEValidationError("image has no sections")
 o=c+20
 if osz<2 or o+osz>len(d): raise PEValidationError("optional header exceeds file bounds")
 magic=u16(d,o)
 if magic!=PROFILES[target][1]: raise PEValidationError("optional-header magic does not match target")
 if osz<(96 if magic==0x10b else 112): raise PEValidationError("optional header too small")
 entry=u32(d,o+16); sa=u32(d,o+32); fa=u32(d,o+36)
 size_image=u32(d,o+56); size_headers=u32(d,o+60); subsystem=u16(d,o+68)
 if subsystem!=10: raise PEValidationError("subsystem is not EFI_APPLICATION (10)")
 if entry==0: raise PEValidationError("entry-point RVA is zero")
 if not sa or sa&(sa-1): raise PEValidationError("section alignment must be a power of two")
 if not fa or fa&(fa-1): raise PEValidationError("file alignment must be a power of two")
 if sa<fa and sa!=fa: raise PEValidationError("section alignment is smaller than file alignment")
 if not size_image or not size_headers or size_headers>len(d): raise PEValidationError("invalid image/header size")
 st=o+osz
 if st+n*40>len(d): raise PEValidationError("section table exceeds file bounds")
 ranges=[]; entry_exec=False
 for i in range(n):
  x=st+i*40
  vs,va,rs,ro=struct.unpack_from("<IIII",d,x+8); flags=u32(d,x+36)
  if rs and (ro<size_headers or ro>len(d) or rs>len(d)-ro): raise PEValidationError("section raw range out of bounds or overlaps headers")
  extent=max(vs,rs)
  if extent:
   if va>0xffffffff-extent: raise PEValidationError("section RVA overflow")
   end=va+extent; ranges.append((va,end,i))
   if va<=entry<end and flags&0x20000000: entry_exec=True
 if not entry_exec: raise PEValidationError("entry point is not inside an executable section")
 ranges.sort()
 for a,b in zip(ranges,ranges[1:]):
  if b[0]<a[1]: raise PEValidationError("overlapping section virtual ranges")
 if any(end>size_image for _,end,_ in ranges): raise PEValidationError("section exceeds SizeOfImage")
 return {"target":target,"machine":hex(machine),"optional_magic":hex(magic),"subsystem":subsystem,"entry_rva":hex(entry),"sections":n}
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument("--target",required=True,choices=sorted(PROFILES)); p.add_argument("image",type=Path); a=p.parse_args()
 try: r=validate_pe(a.image.read_bytes(),a.target)
 except (OSError,PEValidationError) as e: print(f"[EFI PE REJECTED] {a.image}: {e}",file=sys.stderr); return 1
 print("[EFI PE STRUCTURE VALID] "+" ".join(f"{k}={v}" for k,v in r.items()))
 print("NOTE: structural validation only; firmware loading and boot remain unproven.")
 return 0
if __name__=="__main__": raise SystemExit(main())
