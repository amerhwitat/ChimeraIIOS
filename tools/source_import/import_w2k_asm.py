#!/usr/bin/env python3
"""Import a historical W2K-ASM corpus without modifying it.

Usage: tools/source_import/import_w2k_asm.py SOURCE [DEST]
"""
from pathlib import Path
import hashlib, shutil, sys

def main():
    if len(sys.argv) not in (2,3):
        raise SystemExit(__doc__)
    src=Path(sys.argv[1]); dest=Path(sys.argv[2]) if len(sys.argv)==3 else Path('legacy/w2k-asm/W2K-ASM.txt')
    if not src.is_file(): raise SystemExit(f'not found: {src}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src,dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix(dest.suffix+'.sha256').write_text(f'{digest}  {dest.name}\n')
    print(f'imported {dest} sha256={digest}')
if __name__=='__main__': main()
