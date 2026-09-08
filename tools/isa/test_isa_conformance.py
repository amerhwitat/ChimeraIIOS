#!/usr/bin/env python3
"""Conformance tests for the generated ISA bitfield registry.

The tests intentionally separate logical encoding templates from the unchanged
16-byte host ABI. They reject malformed masks and overlapping fields, but do not
invent encodings for incomplete source records.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HEX = re.compile(r"^0x[0-9A-Fa-f]+$")


def fail(msg: str) -> None:
    raise AssertionError(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schema", type=Path)
    args = ap.parse_args()
    doc = json.loads(args.schema.read_text(encoding="utf-8"))
    assert doc["schema"] == "chimera-ii-isa-bitfields"
    assert doc["canonical_abi"]["bytes"] == 16
    assert doc["canonical_abi"]["layout"] == "opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]"
    instructions = doc["instructions"]
    assert doc["instruction_count"] == len(instructions)

    opcodes, mnemonics = set(), set()
    for ins in instructions:
        mnemonic = ins["mnemonic"]
        opcode = int(ins["opcode"], 16)
        if mnemonic in mnemonics:
            fail(f"duplicate mnemonic: {mnemonic}")
        if opcode in opcodes:
            fail(f"duplicate opcode: 0x{opcode:04X}")
        if not 0 <= opcode <= 0xFFFF:
            fail(f"opcode out of 16-bit range: {mnemonic}")
        opcodes.add(opcode); mnemonics.add(mnemonic)

        fields = ins["bitfields"]
        covered = 0
        for field in fields:
            start, end, width = field["start"], field["end"], field["width"]
            assert end >= start >= 0
            assert width == end - start + 1
            mask = int(field["mask"], 16)
            expected = ((1 << width) - 1) << start
            assert mask == expected, f"{mnemonic}.{field['name']}: mask mismatch"
            assert field["shift"] == start
            assert not (covered & mask), f"{mnemonic}: overlapping {field['name']}"
            covered |= mask

        if ins["encoding_status"] == "template":
            assert ins["encoding_template"]
        else:
            assert len(fields) == 5
            assert fields[0]["name"] == "opcode" and fields[0]["width"] == 16
            assert fields[-1]["name"] == "immediate" and fields[-1]["width"] == 64

        example = ins.get("example_binary", "")
        if example:
            assert HEX.match(example), f"{mnemonic}: invalid example_binary"

    # The extension is intentionally sparse: no records are fabricated for 0x00F0..0x0106.
    assert not any(0x00F0 <= int(ins["opcode"], 16) <= 0x0106 and ins["source_ref"] == "internal-extension" for ins in instructions)
    print(f"PASS: {len(instructions)} ISA definitions, unique opcodes, valid masks/shifts, ABI preserved")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
