#!/usr/bin/env python3
"""Fail-closed validator for a target-specific x86-64 native init ELF.

This validates packaging/ELF structure only. It does not establish that an
image is production userspace or that its services work.
"""
import argparse
import struct
import sys
from pathlib import Path

ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
EM_X86_64 = 62
ET_EXEC = 2
PT_LOAD = 1
PF_X = 1
PF_W = 2
PF_R = 4
MAX_IMAGE = 64 * 1024 * 1024
TARGETS = ("live", "installer", "recovery")


def validate(path: Path, target: str) -> None:
    if target not in TARGETS:
        raise ValueError(f"unsupported target {target!r}; expected one of {', '.join(TARGETS)}")
    data = path.read_bytes()
    if not data or len(data) > MAX_IMAGE:
        raise ValueError(f"image size must be between 1 and {MAX_IMAGE} bytes")
    if len(data) < 4 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file; shell scripts are not accepted")
    if len(data) < ELF_HEADER.size:
        raise ValueError("truncated ELF header")
    header = ELF_HEADER.unpack_from(data)
    ident, e_type, machine, _version, entry, phoff, _shoff, _flags, ehsize, phentsize, phnum, *_ = header
    if ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
        raise ValueError("requires ELF64, little-endian, current ELF version")
    if e_type != ET_EXEC:
        raise ValueError("requires a fixed-address ET_EXEC image")
    if machine != EM_X86_64:
        raise ValueError("requires EM_X86_64")
    if ehsize != ELF_HEADER.size or phentsize != PROGRAM_HEADER.size or phnum == 0:
        raise ValueError("invalid ELF/program-header sizes")
    if phoff > len(data) or phnum > (len(data) - phoff) // phentsize:
        raise ValueError("program-header table is out of bounds")

    executable_entry = False
    load_count = 0
    for index in range(phnum):
        p_type, p_flags, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, p_align = PROGRAM_HEADER.unpack_from(
            data, phoff + index * phentsize
        )
        if p_type != PT_LOAD:
            continue
        load_count += 1
        if p_filesz > p_memsz or p_offset > len(data) or p_filesz > len(data) - p_offset:
            raise ValueError(f"PT_LOAD[{index}] has invalid file/memory bounds")
        if p_memsz == 0 or p_vaddr + p_memsz > 0x0000800000000000 or p_vaddr + p_memsz < p_vaddr:
            raise ValueError(f"PT_LOAD[{index}] has invalid user virtual bounds")
        if p_vaddr < 0x0000000100000000:
            raise ValueError(f"PT_LOAD[{index}] is below the supported user address floor")
        if (p_flags & (PF_W | PF_X)) == (PF_W | PF_X):
            raise ValueError(f"PT_LOAD[{index}] violates W^X (writable and executable)")
        if p_align and (p_align & (p_align - 1)):
            raise ValueError(f"PT_LOAD[{index}] alignment is not a power of two")
        if p_flags & PF_X and p_flags & PF_R and p_vaddr <= entry < p_vaddr + p_memsz:
            executable_entry = True
    if load_count == 0:
        raise ValueError("no PT_LOAD segments")
    if not executable_entry:
        raise ValueError("entry point is not inside a readable executable PT_LOAD segment")
    print(f"ELF contract PASS: target={target} role=validated-native-image path={path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=TARGETS)
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    try:
        validate(args.image, args.target)
    except (OSError, ValueError, struct.error) as exc:
        print(f"ELF contract FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
