#!/usr/bin/env python3
"""Fail-closed validation and SHA-256 manifest for production init ELF payloads."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

TARGETS = {
    "live": Path("boot/live/user-init-live.elf"),
    "installer": Path("boot/installer/user-init-installer.elf"),
    "recovery": Path("boot/recovery/user-init-recovery.elf"),
}
MAX_FILE_SIZE = 64 * 1024 * 1024
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
PT_LOAD, PF_X, PF_W = 1, 1, 2

def inspect_elf(path: Path, target: str) -> dict:
    data = path.read_bytes()
    if not data or len(data) > MAX_FILE_SIZE:
        raise ValueError(f"{target}: file size outside 1..{MAX_FILE_SIZE} bytes")
    if len(data) < ELF_HEADER.size:
        raise ValueError(f"{target}: truncated ELF header")
    h = ELF_HEADER.unpack_from(data)
    ident, etype, machine, version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = h
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
        raise ValueError(f"{target}: expected ELF64 little-endian version 1")
    if etype != 2 or machine != 62 or version != 1:
        raise ValueError(f"{target}: expected x86-64 ET_EXEC ELF")
    if ehsize != ELF_HEADER.size or phentsize != PROGRAM_HEADER.size or phnum == 0 or phnum > 128:
        raise ValueError(f"{target}: invalid ELF/program-header dimensions")
    if phoff > len(data) or phnum * phentsize > len(data) - phoff:
        raise ValueError(f"{target}: program-header table exceeds file")
    loads = []
    for i in range(phnum):
        p = PROGRAM_HEADER.unpack_from(data, phoff + i * phentsize)
        p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = p
        if p_type != PT_LOAD:
            continue
        if p_filesz > p_memsz or p_offset > len(data) or p_filesz > len(data) - p_offset:
            raise ValueError(f"{target}: PT_LOAD file/memory bounds invalid")
        if p_memsz == 0 or p_vaddr + p_memsz > 0x0000800000000000 or p_vaddr + p_memsz < p_vaddr:
            raise ValueError(f"{target}: PT_LOAD virtual range invalid/noncanonical")
        if p_flags & PF_W and p_flags & PF_X:
            raise ValueError(f"{target}: writable+executable PT_LOAD violates W^X")
        if p_align > 1 and ((p_align & (p_align - 1)) or p_vaddr % p_align != p_offset % p_align):
            raise ValueError(f"{target}: PT_LOAD alignment invalid")
        loads.append((p_vaddr, p_vaddr + p_memsz, p_flags))
    if not loads or not any((flags & PF_X) and start <= entry < end for start, end, flags in loads):
        raise ValueError(f"{target}: entry point is not inside an executable PT_LOAD segment")
    return {
        "target": target,
        "path": "/" + path.as_posix(),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "elf_class": 64,
        "machine": "x86_64",
        "type": "ET_EXEC",
        "entry": f"0x{entry:x}",
        "load_segments": len(loads),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("iso_root", type=Path, help="root directory of the staged ISO tree")
    parser.add_argument("--write-manifest", type=Path, help="write a JSON SHA-256 manifest after all payloads validate")
    args = parser.parse_args()
    root = args.iso_root
    records = []
    errors = []
    for target, relative in TARGETS.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"{target}: required production init ELF missing: {path}")
            continue
        try:
            records.append(inspect_elf(path, target))
        except (OSError, ValueError, struct.error) as exc:
            errors.append(str(exc))
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        print("Production init ELF validation failed; refusing ISO publication.", file=sys.stderr)
        return 1
    manifest = {"schema_version": 1, "contract": "koronos.production-init-elfs", "status": "payloads-validated-not-runtime-accepted", "payloads": records}
    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.write_manifest:
        args.write_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.write_manifest.write_text(encoded, encoding="utf-8")
    for record in records:
        print(f"PASS: target={record['target']} size={record['size_bytes']} sha256={record['sha256']} entry={record['entry']}")
    print("PASS: production init ELF payload structure and checksums validated; runtime acceptance remains a separate gate.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
