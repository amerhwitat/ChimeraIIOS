#!/usr/bin/env python3
"""Identify executable/container formats without claiming instruction-set support.

This is a format and target-identity probe, not a disassembler or emulator.
Unknown and raw byte streams remain unknown rather than being guessed from
short opcode-like prefixes.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

ELF_MACHINES = {
    3: "x86",
    8: "mips",
    20: "powerpc",
    21: "powerpc64",
    40: "arm",
    42: "superh",
    43: "sparc-v9",
    50: "ia64",
    62: "x86_64",
    183: "aarch64",
    243: "riscv",
    258: "loongarch",
}
PE_MACHINES = {
    0x014C: "x86",
    0x8664: "x86_64",
    0x01C0: "arm",
    0x01C4: "armv7",
    0xAA64: "aarch64",
    0x5032: "riscv32",
    0x5064: "riscv64",
    0x5128: "loongarch64",
}
MACHO_CPU = {
    7: "x86",
    0x01000007: "x86_64",
    12: "arm",
    0x0100000C: "aarch64",
    18: "powerpc",
    0x01000012: "powerpc64",
}


def _result(fmt: str, arch: str | None, *, bits: int | None = None,
            endian: str | None = None, confidence: str = "signature",
            details: str = "") -> dict[str, Any]:
    return {
        "format": fmt,
        "architecture": arch or "unknown",
        "bits": bits,
        "endianness": endian or "unknown",
        "identification_confidence": confidence,
        "execution_support": "not_assessed",
        "details": details,
    }


def identify(data: bytes) -> dict[str, Any]:
    """Return conservative format/architecture metadata for bytes."""
    if data.startswith(b"\x7fELF"):
        if len(data) < 20:
            return _result("ELF", None, confidence="truncated", details="ELF header shorter than e_machine field")
        elf_class, encoding = data[4], data[5]
        if elf_class not in (1, 2) or encoding not in (1, 2):
            return _result("ELF", None, confidence="malformed", details="invalid ELF class or byte order")
        endian = "little" if encoding == 1 else "big"
        machine = int.from_bytes(data[18:20], endian)
        return _result("ELF", ELF_MACHINES.get(machine), bits=32 if elf_class == 1 else 64,
                       endian=endian, details=f"e_machine={machine}; unknown machine IDs are not guessed")

    if data.startswith(b"MZ"):
        if len(data) < 64:
            return _result("DOS/PE", None, confidence="truncated", details="MZ header too short to contain e_lfanew")
        pe_offset = int.from_bytes(data[0x3C:0x40], "little")
        if pe_offset <= len(data) - 6 and data[pe_offset:pe_offset + 4] == b"PE\0\0":
            machine = int.from_bytes(data[pe_offset + 4:pe_offset + 6], "little")
            return _result("PE", PE_MACHINES.get(machine), details=f"COFF Machine=0x{machine:04x}")
        return _result("DOS MZ", "x86", bits=16, endian="little",
                       details="MZ executable signature; actual CPU mode and compatibility are not validated")

    if len(data) >= 8 and data[:4] == b"\0asm":
        version = int.from_bytes(data[4:8], "little")
        return _result("WebAssembly", "wasm32" if version == 1 else None, bits=32,
                       endian="little", details=f"module_version={version}")

    if len(data) >= 8:
        magic = data[:4]
        macho = {
            b"\xfe\xed\xfa\xce": ("big", 32), b"\xce\xfa\xed\xfe": ("little", 32),
            b"\xfe\xed\xfa\xcf": ("big", 64), b"\xcf\xfa\xed\xfe": ("little", 64),
        }
        if magic in macho:
            endian, bits = macho[magic]
            cpu = int.from_bytes(data[4:8], endian)
            return _result("Mach-O", MACHO_CPU.get(cpu), bits=bits, endian=endian,
                           details=f"cputype=0x{cpu:08x}")
        fat_macho = {
            b"\xca\xfe\xba\xbe": ("big", 32), b"\xbe\xba\xfe\xca": ("little", 32),
            b"\xca\xfe\xba\xbf": ("big", 64), b"\xbf\xba\xfe\xca": ("little", 64),
        }
        if magic in fat_macho:
            endian, bits = fat_macho[magic]
            count = int.from_bytes(data[4:8], endian)
            return _result("Mach-O universal/fat", None, bits=bits, endian=endian,
                           details=f"architecture_slices={count}; slice table not yet enumerated")

    return _result("raw/unknown", None, confidence="none",
                   details="No recognized container signature; instruction-set identification requires a target hint or validated decoder")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON (default)")
    args = parser.parse_args()
    try:
        result = identify(args.file.read_bytes())
    except OSError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
