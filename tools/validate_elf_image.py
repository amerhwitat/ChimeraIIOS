#!/usr/bin/env python3
"""Fail-closed ELF header/program-header validator; not a boot acceptance test."""
from __future__ import annotations
import argparse
import struct
import sys
from pathlib import Path

MACHINES = {"x86_64": 62, "aarch64": 183, "riscv64": 243, "x86": 3}
CLASSES = {"x86": 1, "x86_64": 2, "aarch64": 2, "riscv64": 2}
ET_EXEC, ET_DYN, PT_LOAD = 2, 3, 1
ELFMAG = b"\x7fELF"

class ELFValidationError(ValueError):
    pass

def validate_elf(data: bytes, target: str) -> dict:
    if target not in MACHINES:
        raise ELFValidationError(f"unsupported target profile: {target}")
    if len(data) < 16 or data[:4] != ELFMAG:
        raise ELFValidationError("missing/truncated ELF identification")
    elf_class, encoding, version = data[4], data[5], data[6]
    if elf_class != CLASSES[target]:
        raise ELFValidationError(f"ELF class {elf_class} does not match {target}")
    if encoding not in (1, 2):
        raise ELFValidationError("invalid ELF data encoding")
    if version != 1:
        raise ELFValidationError("unsupported ELF identification version")
    endian = "<" if encoding == 1 else ">"
    is64 = elf_class == 2
    header_fmt = endian + ("HHIQQQIHHHHHH" if is64 else "HHIIIIIHHHHHH")
    header_size = struct.calcsize(header_fmt)
    if len(data) < 16 + header_size:
        raise ELFValidationError("truncated ELF header")
    fields = struct.unpack_from(header_fmt, data, 16)
    e_type, machine, e_version, e_entry, e_phoff = fields[:5]
    e_ehsize, e_phentsize, e_phnum = fields[7], fields[8], fields[9]
    if machine != MACHINES[target]:
        raise ELFValidationError(f"e_machine {machine} does not match {target} ({MACHINES[target]})")
    if e_type not in (ET_EXEC, ET_DYN):
        raise ELFValidationError(f"ELF type {e_type} is not ET_EXEC or ET_DYN")
    if e_version != 1 or e_ehsize < 16 + header_size:
        raise ELFValidationError("invalid ELF version/header size")
    ph_fmt = endian + ("IIQQQQQQ" if is64 else "IIIIIIII")
    expected_ph_size = struct.calcsize(ph_fmt)
    if e_phnum == 0 or e_phentsize < expected_ph_size:
        raise ELFValidationError("missing or undersized program-header table")
    if e_phoff > len(data) or e_phnum > (len(data) - e_phoff) // e_phentsize:
        raise ELFValidationError("program-header table exceeds file bounds")
    loads = []
    for index in range(e_phnum):
        off = e_phoff + index * e_phentsize
        p = struct.unpack_from(ph_fmt, data, off)
        if is64:
            p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = p
        else:
            p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = p
        if p_type != PT_LOAD:
            continue
        if p_filesz > p_memsz:
            raise ELFValidationError(f"PT_LOAD[{index}] filesz exceeds memsz")
        if p_offset > len(data) or p_filesz > len(data) - p_offset:
            raise ELFValidationError(f"PT_LOAD[{index}] file range exceeds file bounds")
        if p_align not in (0, 1) and p_align & (p_align - 1):
            raise ELFValidationError(f"PT_LOAD[{index}] alignment is not a power of two")
        if p_align > 1 and p_offset % p_align != p_vaddr % p_align:
            raise ELFValidationError(f"PT_LOAD[{index}] offset/vaddr alignment incongruent")
        if p_memsz and p_vaddr + p_memsz < p_vaddr:
            raise ELFValidationError(f"PT_LOAD[{index}] address range overflows")
        if p_memsz:
            loads.append((p_vaddr, p_vaddr + p_memsz, index))
    if not loads:
        raise ELFValidationError("no PT_LOAD segments")
    if not any(start <= e_entry < end for start, end, _ in loads):
        raise ELFValidationError("entry point is not inside a PT_LOAD memory range")
    loads.sort()
    for previous, current in zip(loads, loads[1:]):
        if current[0] < previous[1]:
            raise ELFValidationError(f"overlapping PT_LOAD virtual ranges: {previous[2]} and {current[2]}")
    return {"target": target, "class": elf_class, "endianness": "little" if encoding == 1 else "big",
            "machine": machine, "type": e_type, "entry": e_entry, "load_segments": len(loads)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(MACHINES))
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    try:
        result = validate_elf(args.elf.read_bytes(), args.target)
    except (OSError, ELFValidationError) as exc:
        print(f"[ELF REJECTED] {args.elf}: {exc}", file=sys.stderr)
        return 1
    print("[ELF STRUCTURE VALID] " + " ".join(f"{k}={v}" for k, v in result.items()))
    print("NOTE: structural validation only; does not prove ABI correctness, boot, or runtime acceptance.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
