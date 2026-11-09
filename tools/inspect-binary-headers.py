#!/usr/bin/env python3
"""Identify executable/container formats and basic CPU headers without executing them."""
import argparse
import json
import struct
from pathlib import Path

ELF_MACHINES = {
    3: "i386", 8: "MIPS", 20: "PowerPC", 21: "PowerPC64",
    22: "s390", 40: "ARM", 42: "SuperH", 43: "SPARCv9",
    50: "IA-64", 62: "x86_64", 183: "AArch64",
    243: "RISC-V", 258: "LoongArch",
}
PE_MACHINES = {
    0x014C: "i386", 0x8664: "x86_64", 0x01C0: "ARM",
    0x01C4: "ARMv7", 0xAA64: "AArch64", 0x0200: "IA-64",
    0x5032: "RISC-V32", 0x5064: "RISC-V64", 0x5128: "RISC-V128",
}
MACH_CPUS = {
    7: "i386", 0x01000007: "x86_64", 12: "ARM",
    0x0100000C: "AArch64", 18: "PowerPC",
    0x01000012: "PowerPC64",
}

def result(fmt, os_name, arch="unknown", bits=None, endian=None, **extra):
    return {"format": fmt, "os": os_name, "architecture": arch,
            "bits": bits, "endianness": endian, **extra}

def inspect(data):
    if data.startswith(b"\x7fELF") and len(data) >= 20:
        cls, enc, abi = data[4], data[5], data[7]
        endian = "little" if enc == 1 else "big" if enc == 2 else "unknown"
        order = "<" if enc == 1 else ">" if enc == 2 else "="
        machine = struct.unpack(order + "H", data[18:20])[0]
        return result("ELF", "Unix/Linux", ELF_MACHINES.get(machine, f"EM_{machine}"),
                      32 if cls == 1 else 64 if cls == 2 else None, endian,
                      os_abi=abi, elf_class=cls)
    if data.startswith(b"MZ") and len(data) >= 64:
        pe_offset = struct.unpack("<I", data[0x3C:0x40])[0]
        if pe_offset + 6 <= len(data) and data[pe_offset:pe_offset+4] == b"PE\0\0":
            machine = struct.unpack("<H", data[pe_offset+4:pe_offset+6])[0]
            return result("PE/COFF", "Windows", PE_MACHINES.get(machine, f"PE_MACHINE_{machine:#x}"),
                          64 if machine in (0x8664, 0xAA64, 0x5064, 0x5128) else 32,
                          "little", machine=f"{machine:#06x}")
        return result("DOS MZ", "DOS", "x86", 16, "little", note="MZ header; not a PE image")
    if len(data) >= 8:
        magic = data[:4]
        mach = {
            b"\xfe\xed\xfa\xce": ("big", 32),
            b"\xce\xfa\xed\xfe": ("little", 32),
            b"\xfe\xed\xfa\xcf": ("big", 64),
            b"\xcf\xfa\xed\xfe": ("little", 64),
        }
        if magic in mach:
            endian, bits = mach[magic]
            order = ">" if endian == "big" else "<"
            cpu = struct.unpack(order + "I", data[4:8])[0]
            return result("Mach-O", "macOS/Darwin", MACH_CPUS.get(cpu, f"CPU_{cpu:#x}"),
                          bits, endian, cpu_type=f"{cpu:#x}")
        if magic == bytes.fromhex("cafebabe"):
            java_version = struct.unpack(">I", data[4:8])[0]
            if java_version > 16:
                return result("Java Class", "JVM", "bytecode", None, "big",
                              major_version=java_version)
        fat = {b"\xca\xfe\xba\xbe": "big", b"\xbe\xba\xfe\xca": "little"}
        if magic in fat:
            endian = fat[magic]
            order = ">" if endian == "big" else "<"
            count = struct.unpack(order + "I", data[4:8])[0]
            return result("Mach-O Universal", "macOS/Darwin", "multiple", None, endian,
                          architecture_count=count)
    if data.startswith(b"\0asm"):
        return result("WebAssembly", "WASI/Web", "wasm", 32, "little")
    if data.startswith(b"\xca\xfe\xba\xbe"):
        return result("Java Class", "JVM", "bytecode", None, "big")
    return result("unknown", "unknown", note="No recognized executable header")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    reports = []
    failed = False
    for path in args.files:
        try:
            data = path.read_bytes()[:4096]
            reports.append({"path": str(path), **inspect(data)})
        except OSError as exc:
            failed = True
            reports.append({"path": str(path), "error": str(exc)})
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for item in reports:
            if "error" in item:
                print(f"{item['path']}: ERROR: {item['error']}")
            else:
                print(f"{item['path']}: {item['format']} | {item['os']} | "
                      f"{item['architecture']} | {item['bits'] or '?'}-bit | "
                      f"{item['endianness'] or 'unknown'} endian")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
