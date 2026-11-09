#!/usr/bin/env python3
"""Safely identify ELF, PE/COFF, Mach-O and WebAssembly headers without executing files."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys

MACH = {
    0x00000007: "x86",
    0x01000007: "x86-64",
    0x0000000C: "ARM",
    0x0100000C: "AArch64",
    0x01000012: "PowerPC64",
}
PE = {0x014C: "x86", 0x8664: "x86-64", 0x01C0: "ARM",
      0x01C4: "ARMv7", 0xAA64: "AArch64", 0x5064: "RISC-V 64",
      0x5032: "RISC-V 32", 0x6264: "LoongArch 64"}
ELF = {3: "x86", 8: "MIPS", 20: "PowerPC", 21: "PowerPC64",
       22: "S390", 40: "ARM", 62: "x86-64", 183: "AArch64",
       243: "RISC-V", 258: "LoongArch"}
MACH_MAGICS = {
    b"\xfe\xed\xfa\xce": ("big", 32), b"\xce\xfa\xed\xfe": ("little", 32),
    b"\xfe\xed\xfa\xcf": ("big", 64), b"\xcf\xfa\xed\xfe": ("little", 64),
}
FAT_MAGICS = {
    b"\xca\xfe\xba\xbe": ("big", 32), b"\xbe\xba\xfe\xca": ("little", 32),
    b"\xca\xfe\xba\xbf": ("big", 64), b"\xbf\xba\xfe\xca": ("little", 64),
}

def parse(path: Path) -> dict:
    size = path.stat().st_size
    if not path.is_file() or size < 4:
        raise ValueError("not a regular binary file or header is truncated")
    with path.open("rb") as f:
        head = f.read(64)
        if head[:4] == b"\x7fELF":
            if len(head) < 20 or head[4] not in (1, 2) or head[5] not in (1, 2):
                raise ValueError("invalid or truncated ELF identification")
            endian = "<" if head[5] == 1 else ">"
            bits = 32 if head[4] == 1 else 64
            etype, machine = struct.unpack_from(endian + "HH", head, 16)
            return {"format": "ELF", "bits": bits, "endianness": "little" if endian == "<" else "big",
                    "machine_id": machine, "architecture": ELF.get(machine, f"unknown ({machine})"),
                    "object_type": {1:"relocatable",2:"executable",3:"shared-object",4:"core"}.get(etype, f"unknown ({etype})"),
                    "file_size": size, "executed": False}
        if head[:2] == b"MZ":
            if len(head) < 64:
                raise ValueError("truncated DOS/PE header")
            offset = struct.unpack_from("<I", head, 0x3C)[0]
            if offset > 1024 * 1024 or offset + 24 > size:
                raise ValueError("PE header offset is outside file or exceeds 1 MiB safety bound")
            f.seek(offset)
            pe = f.read(24)
            if len(pe) < 24 or pe[:4] != b"PE\0\0":
                raise ValueError("MZ executable has no valid PE signature (possibly DOS-only)")
            machine, sections, _, _, _, optional_size, characteristics = struct.unpack_from("<HHIIIHH", pe, 4)
            optional = f.read(min(optional_size, 256))
            if len(optional) < 2:
                raise ValueError("truncated PE optional header")
            magic = struct.unpack_from("<H", optional, 0)[0]
            if magic not in (0x10B, 0x20B):
                raise ValueError(f"unsupported PE optional-header magic 0x{magic:04x}")
            subsystem = struct.unpack_from("<H", optional, 68)[0] if len(optional) >= 70 else None
            return {"format": "PE/COFF", "bits": 32 if magic == 0x10B else 64,
                    "machine_id": machine, "architecture": PE.get(machine, f"unknown (0x{machine:04x})"),
                    "sections": sections, "subsystem_id": subsystem,
                    "subsystem": {1:"native",2:"Windows GUI",3:"Windows console",10:"EFI application",11:"EFI boot service driver",12:"EFI runtime driver"}.get(subsystem, "unknown"),
                    "characteristics": characteristics, "file_size": size, "executed": False}
        if head[:4] in MACH_MAGICS:
            endian_name, bits = MACH_MAGICS[head[:4]]
            endian = "<" if endian_name == "little" else ">"
            if len(head) < 28:
                raise ValueError("truncated Mach-O header")
            cpu, subtype, filetype, ncmds, sizeofcmds, flags = struct.unpack_from(endian + "IIIIII", head, 4)
            return {"format": "Mach-O", "bits": bits, "endianness": endian_name,
                    "machine_id": cpu, "architecture": MACH.get(cpu, f"unknown ({cpu})"),
                    "file_type_id": filetype, "load_commands": ncmds, "load_commands_size": sizeofcmds,
                    "flags": flags, "file_size": size, "executed": False}
        if head[:4] in FAT_MAGICS:
            endian_name, bits = FAT_MAGICS[head[:4]]
            endian = "<" if endian_name == "little" else ">"
            count = struct.unpack_from(endian + "I", head, 4)[0]
            entry_size = 20 if bits == 32 else 32
            if count < 1 or count > 64 or 8 + count * entry_size > size:
                raise ValueError("invalid or truncated universal Mach-O architecture table")
            f.seek(8)
            table = f.read(count * entry_size)
            archs = []
            for i in range(count):
                cpu = struct.unpack_from(endian + "I", table, i * entry_size)[0]
                archs.append(MACH.get(cpu, f"unknown ({cpu})"))
            return {"format": "Mach-O universal", "endianness": endian_name,
                    "architectures": archs, "architecture_count": count,
                    "file_size": size, "executed": False}
        if head[:4] == b"\0asm":
            return {"format": "WebAssembly", "version": struct.unpack_from("<I", head, 4)[0] if len(head) >= 8 else None,
                    "file_size": size, "executed": False}
        raise ValueError("unrecognized executable/object format (magic bytes do not match ELF, PE, Mach-O or WASM)")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = p.parse_args()
    results = []
    failed = False
    for path in args.files:
        try:
            item = {"path": str(path), **parse(path)}
            results.append(item)
            if not args.json:
                print(f"{path}: {item['format']} {item.get('bits', '')} {item.get('architecture', item.get('architectures', ''))} (inspection only; not executed)")
        except (OSError, ValueError, struct.error) as exc:
            failed = True
            results.append({"path": str(path), "error": str(exc)})
            if not args.json:
                print(f"{path}: ERROR: {exc}", file=sys.stderr)
    if args.json:
        print(json.dumps(results, indent=2))
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
