#!/usr/bin/env python3
"""Unit tests for the Chimera native CISC/RISC codecs and CHMOBJ1 container.

These are engineering tests. They deliberately do not assert official
conformance or change the universal catalogue's not_implemented counts.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "isa"))

from chimera_native_isa import (  # noqa: E402
    BACKENDS, CATALOG_VECTORS, IllegalInstruction, ObjectFormatError, State,
    assemble, build_object, demo_object, disassemble, effects, step,
    validate_object, SECTION_STRUCT, PERM_EXEC, PERM_READ, SECTION_TYPES, Section, Symbol,
)
from run_native_isa_conformance import ILLEGAL, VECTORS, run as run_conformance  # noqa: E402

UNIVERSAL = ROOT / "isa" / "generated" / "universal-instruction-catalog.json"
NATIVE_CATALOG = ROOT / "isa" / "generated" / "chimera-native-isa-catalog.json"
FORMATS = ROOT / "tools" / "chimera-asm" / "chimera_native_formats.json"


@pytest.mark.parametrize("arch", sorted(BACKENDS))
def test_backend_has_formats(arch):
    formats = BACKENDS[arch].formats()
    assert formats
    assert all("bit_fields" in spec and "format_class" in spec for spec in formats.values())


@pytest.mark.parametrize("key,text", sorted(CATALOG_VECTORS.items()))
def test_catalog_vector_roundtrip_and_mask(key, text):
    arch, mnemonic, form = key
    row = next(r for r in json.loads(UNIVERSAL.read_text())["instructions"]
               if r["architecture"] == arch and r["mnemonic"] == mnemonic and r["form_id"] == form)
    decoded = assemble(arch, text)
    back = disassemble(arch, decoded.data)
    order = "big" if arch == "x86-64" else "little"
    word = int.from_bytes(decoded.data, order)
    mask = int(row["mask_bits"], 2)
    value = int(row["value_bits"], 2)
    assert (word & mask) == (value & mask)
    assert back.text == decoded.text
    assert effects(arch, decoded)["registers_written"] is not None


@pytest.mark.parametrize("vec", VECTORS, ids=lambda v: v.name)
def test_execution_vector(vec):
    state = State.zeros(16 if vec.arch == "x86-64" else 32, 8192)
    aliases = {"x86-64": {"RAX": 0, "RBX": 3, "RCX": 1, "RDX": 2, "RSP": 4},
               "aarch64": {f"X{n}": n for n in range(31)},
               "riscv64": {f"x{n}": n for n in range(32)}}[vec.arch]
    for name, value in vec.init_regs.items():
        state.regs[aliases[name]] = value & ((1 << 64) - 1)
    state.flags.update(vec.init_flags)
    for address, (value, width) in vec.init_memory.items():
        state.write_mem(address, width, value)
    decoded = [assemble(vec.arch, line) for line in vec.lines]
    offsets = []
    blob = bytearray()
    for item in decoded:
        offsets.append(len(blob))
        blob.extend(item.data)
    state.memory[0:len(blob)] = blob
    by_pc = dict(zip(offsets, decoded))
    steps = 0
    while state.pc in by_pc and steps < 32 and not state.halted:
        step(vec.arch, by_pc[state.pc], state)
        steps += 1
    for name, expected in vec.expected_regs.items():
        assert state.regs[aliases[name]] == (expected & ((1 << 64) - 1)), name
    for name, expected in vec.expected_flags.items():
        assert state.flags.get(name) == expected, name
    for address, (expected, width) in vec.expected_memory.items():
        assert state.read_mem(address, width) == (expected & ((1 << (8 * width)) - 1))
    if vec.expected_pc is not None:
        assert state.pc == vec.expected_pc
    assert state.trap == vec.expected_trap


@pytest.mark.parametrize("arch,name,blob", ILLEGAL)
def test_illegal_encodings_rejected(arch, name, blob):
    with pytest.raises(IllegalInstruction):
        disassemble(arch, blob)


@pytest.mark.parametrize("arch", ["x86-64", "aarch64", "riscv64"])
def test_object_roundtrip(arch):
    line = {"x86-64": "ADD [RAX],RAX", "aarch64": "ADD X0,X1,X2", "riscv64": "ADDI x1,x2,5"}[arch]
    obj = validate_object(demo_object(arch, line), expected_arch=arch)
    assert obj.arch == arch
    assert any(s.name == ".text" for s in obj.sections)
    assert any(s.name == ".strtab" for s in obj.sections)
    assert any(s.name == "__start" or s.name == "entry" for s in obj.symbols)


def test_object_rejects_digest_mismatch():
    blob = bytearray(demo_object("riscv64"))
    blob[-1] ^= 1
    with pytest.raises(ObjectFormatError):
        validate_object(bytes(blob))


def test_object_rejects_bad_alignment():
    body = bytearray(demo_object("riscv64")[:-32])
    at = 64 + SECTION_STRUCT.size + 6  # section 1 align byte
    body[at] = 3
    with pytest.raises(ObjectFormatError):
        validate_object(bytes(body) + hashlib.sha256(bytes(body)).digest())


def test_generated_catalog_integrity():
    universal = json.loads(UNIVERSAL.read_text())
    derived = json.loads(NATIVE_CATALOG.read_text())
    formats = json.loads(FORMATS.read_text())
    assert universal["coverage"]["conformance_tested"] == 0
    assert universal["coverage"]["not_implemented"] == 1613
    assert derived["inventory"]["architecture_inventory_count"] == 104
    assert derived["inventory"]["instruction_record_count"] == 1613
    assert derived["inventory"]["real_backend_instruction_rows"] == len(CATALOG_VECTORS)
    assert derived["inventory"]["descriptors_only_or_not_implemented_instruction_rows"] == 1613 - len(CATALOG_VECTORS)
    assert len(derived["architectures"]) == 104
    assert len(derived["instructions"]) == 1613
    assert all(row["semantics"]["owner"] for row in derived["instructions"])
    assert all(row["native_format"]["semantics_owner"] for row in derived["instructions"])
    assert formats["extends"]["format"] == "CHM-ISA-1"
    assert len(formats["inventory_architectures"]) == 104


def test_conformance_runner_is_all_green_and_honest():
    evidence = run_conformance()
    assert evidence["failed_checks"] == 0
    assert evidence["official_catalog"]["coverage"]["conformance_tested"] == 0
    assert evidence["official_catalog"]["coverage"]["not_implemented"] == 1613
    assert evidence["status"] == "partial-engineering-evidence-only"
