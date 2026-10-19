#!/usr/bin/env python3
"""Validate the structure of production Koronos user-init ELF64 payloads.

ELF structure validation is necessary but not sufficient for acceptance. This
script deliberately does not claim ring-3 execution, service readiness, or SMP.
"""
from __future__ import annotations
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAYLOAD_DIR = ROOT / "build/koronos/userspace"
TARGETS = ("live", "installer", "recovery")
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
PT_LOAD, PF_X, PF_W, EM_X86_64, ET_EXEC = 1, 1, 2, 62, 2
MAX_FILE_SIZE, MAX_PROGRAM_HEADERS = 64 * 1024 * 1024, 128


def validate(path: pathlib.Path) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"{path}: cannot read payload: {exc}"]
    errors: list[str] = []
    if not data or len(data) > MAX_FILE_SIZE:
        return [f"{path}: empty or oversized ELF ({len(data)} bytes)"]
    if len(data) < ELF_HEADER.size:
        return [f"{path}: truncated ELF header"]
    fields = ELF_HEADER.unpack_from(data)
    ident, e_type, e_machine, _version, entry, phoff, _shoff, _flags, ehsize, phentsize, phnum, *_ = fields
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
        errors.append(f"{path}: expected ELF64, little-endian, current-version image")
    if e_type != ET_EXEC:
        errors.append(f"{path}: expected ET_EXEC, got e_type={e_type}")
    if e_machine != EM_X86_64:
        errors.append(f"{path}: expected x86-64 (EM_X86_64=62), got {e_machine}")
    if ehsize < ELF_HEADER.size or phentsize < PROGRAM_HEADER.size:
        errors.append(f"{path}: invalid ELF/program-header entry size")
    if phnum == 0 or phnum > MAX_PROGRAM_HEADERS:
        errors.append(f"{path}: invalid program-header count {phnum}")
    table_end = phoff + phentsize * phnum
    if phoff < ehsize or table_end < phoff or table_end > len(data):
        errors.append(f"{path}: program-header table is out of file bounds")
        return errors
    load_count = 0
    executable_ranges: list[tuple[int, int]] = []
    for index in range(phnum):
        off = phoff + index * phentsize
        p_type, p_flags, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, p_align = PROGRAM_HEADER.unpack_from(data, off)
        if p_type != PT_LOAD:
            continue
        load_count += 1
        if p_filesz > p_memsz:
            errors.append(f"{path}: PT_LOAD[{index}] filesz exceeds memsz")
        end = p_offset + p_filesz
        if end < p_offset or end > len(data):
            errors.append(f"{path}: PT_LOAD[{index}] file range is out of bounds")
        if p_align not in (0, 1) and p_align & (p_align - 1):
            errors.append(f"{path}: PT_LOAD[{index}] alignment is not a power of two")
        if p_flags & PF_W and p_flags & PF_X:
            errors.append(f"{path}: PT_LOAD[{index}] violates W^X")
        if p_flags & PF_X:
            executable_ranges.append((p_vaddr, p_vaddr + p_memsz))
    if load_count == 0:
        errors.append(f"{path}: no PT_LOAD segments")
    if not any(start <= entry < end for start, end in executable_ranges):
        errors.append(f"{path}: entry point 0x{entry:x} is not in an executable PT_LOAD segment")
    if not errors:
        print(f"ELF STRUCTURE PASS: {path.name} ({len(data)} bytes, entry=0x{entry:x}, PT_LOAD={load_count})")
    return errors


def main() -> int:
    errors: list[str] = []
    for target in TARGETS:
        errors.extend(validate(PAYLOAD_DIR / f"{target}-init.elf"))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("NOT ACCEPTED: structural validation is not runtime acceptance.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
