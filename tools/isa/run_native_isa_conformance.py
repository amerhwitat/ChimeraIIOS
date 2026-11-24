#!/usr/bin/env python3
"""Measured, honest conformance runner for the Chimera native ISA slice.

This runner performs REAL encoding, disassembly, execution, register/flag
comparison, illegal-instruction rejection, native-vs-emulator cross-checks and
object validation. Its results are engineering evidence only. It never changes
the official universal catalogue: conformance_tested remains 0 and
not_implemented remains 1613 unless a genuinely complete all-entry run exists,
which this partial vertical slice is not.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "isa"))
from chimera_native_isa import (  # noqa: E402
    CATALOG_VECTORS, IllegalInstruction, ObjectFormatError, State, SECTION_STRUCT, assemble,
    build_object, demo_object, disassemble, effects, step, validate_object,
    PERM_EXEC, PERM_READ, SECTION_TYPES, Section, Symbol,
)
UNIVERSAL = ROOT / "isa" / "generated" / "universal-instruction-catalog.json"
NATIVE_CATALOG = ROOT / "isa" / "generated" / "chimera-native-isa-catalog.json"
DEFAULT_OUTPUT = ROOT / "isa" / "generated" / "native-isa-conformance-evidence.json"

REG_ALIASES = {
    "x86-64": {"RAX": 0, "RBX": 3, "RCX": 1, "RDX": 2, "RSP": 4, "RBP": 5, "RSI": 6, "RDI": 7},
    "aarch64": {f"X{n}": n for n in range(31)},
    "riscv64": {f"x{n}": n for n in range(32)},
}


@dataclass
class Vector:
    name: str
    arch: str
    lines: list[str]
    init_regs: dict[str, int] = field(default_factory=dict)
    init_flags: dict[str, int] = field(default_factory=dict)
    init_memory: dict[int, tuple[int, int]] = field(default_factory=dict)
    expected_regs: dict[str, int] = field(default_factory=dict)
    expected_flags: dict[str, int] = field(default_factory=dict)
    expected_memory: dict[int, tuple[int, int]] = field(default_factory=dict)
    expected_pc: int | None = None
    expected_trap: str | None = None


VECTORS: list[Vector] = [
    Vector("x86-add-register-flags", "x86-64", ["ADD RAX,RBX"],
           {"RAX": 5, "RBX": 7}, expected_regs={"RAX": 12, "RBX": 7},
           expected_flags={"ZF": 0, "CF": 0, "SF": 0, "OF": 0, "PF": 1}, expected_pc=3),
    Vector("x86-sub-borrow", "x86-64", ["SUB RAX,RBX"],
           {"RAX": 5, "RBX": 7}, expected_regs={"RAX": (1 << 64) - 2},
           expected_flags={"CF": 1, "SF": 1, "ZF": 0}, expected_pc=3),
    Vector("x86-cmp-equal-zero-flag", "x86-64", ["CMP RAX,RBX"],
           {"RAX": 7, "RBX": 7}, expected_regs={"RAX": 7, "RBX": 7},
           expected_flags={"ZF": 1, "CF": 0}, expected_pc=3),
    Vector("x86-bitwise-and", "x86-64", ["AND RAX,RBX"],
           {"RAX": 0xF0, "RBX": 0x3C}, expected_regs={"RAX": 0x30}, expected_pc=3),
    Vector("x86-bitwise-or-xor", "x86-64", ["OR RAX,RBX", "XOR RAX,RBX"],
           {"RAX": 0xF0, "RBX": 0x3C}, expected_regs={"RAX": 0xC0}, expected_pc=6),
    Vector("x86-mov-load", "x86-64", ["MOV RAX,[RBX]"],
           {"RBX": 0x100}, init_memory={0x100: (0x1122334455667788, 8)},
           expected_regs={"RAX": 0x1122334455667788}, expected_pc=3),
    Vector("x86-mov-store", "x86-64", ["MOV [RBX],RAX"],
           {"RBX": 0x200, "RAX": 0x1234}, expected_memory={0x200: (0x1234, 8)}, expected_pc=3),
    Vector("x86-push-pop", "x86-64", ["PUSH RAX", "POP RCX"],
           {"RAX": 0x42, "RSP": 0x800}, expected_regs={"RCX": 0x42, "RSP": 0x800},
           expected_memory={0x7F8: (0x42, 8)}, expected_pc=2),
    Vector("x86-call-stack", "x86-64", ["CALL 0"],
           {"RSP": 0x800}, expected_regs={"RSP": 0x7F8},
           expected_memory={0x7F8: (5, 8)}, expected_pc=5),
    Vector("x86-ret-stack", "x86-64", ["RET"],
           {"RSP": 0x800}, init_memory={0x800: (0x10, 8)},
           expected_regs={"RSP": 0x808}, expected_pc=0x10),
    Vector("x86-jmp-relative", "x86-64", ["JMP 4", "NOP"],
           expected_pc=9),
    Vector("a64-add-register", "aarch64", ["ADD X0,X1,X2"],
           {"X1": 5, "X2": 7}, expected_regs={"X0": 12}, expected_pc=4),
    Vector("a64-sub-immediate", "aarch64", ["SUB X0,X1,#1"],
           {"X1": 10}, expected_regs={"X0": 9}, expected_pc=4),
    Vector("a64-logical", "aarch64", ["AND X0,X1,X2", "ORR X3,X1,X2", "EOR X4,X1,X2"],
           {"X1": 0xF0, "X2": 0x3C},
           expected_regs={"X0": 0x30, "X3": 0xFC, "X4": 0xCC}, expected_pc=12),
    Vector("a64-load-store", "aarch64", ["LDR X0,[X1,#0]", "STR X0,[X1,#8]"],
           {"X1": 0x100}, init_memory={0x100: (0x1122334455667788, 8)},
           expected_regs={"X0": 0x1122334455667788},
           expected_memory={0x108: (0x1122334455667788, 8)}, expected_pc=8),
    Vector("a64-bl-link", "aarch64", ["BL 4"],
           expected_regs={"X30": 4}, expected_pc=8),
    Vector("a64-br-register", "aarch64", ["BR X1"],
           {"X1": 0x40}, expected_pc=0x40),
    Vector("a64-ret-register", "aarch64", ["RET X30"],
           {"X30": 0x30}, expected_pc=0x30),
    Vector("a64-svc-trap", "aarch64", ["SVC #7"],
           expected_trap="SVC #7", expected_pc=4),
    Vector("rv64-add-register", "riscv64", ["ADD x1,x2,x3"],
           {"x2": 5, "x3": 7}, expected_regs={"x1": 12}, expected_pc=4),
    Vector("rv64-sub-register", "riscv64", ["SUB x1,x2,x3"],
           {"x2": 5, "x3": 7}, expected_regs={"x1": (1 << 64) - 2}, expected_pc=4),
    Vector("rv64-add-immediate", "riscv64", ["ADDI x1,x2,5"],
           {"x2": 10}, expected_regs={"x1": 15}, expected_pc=4),
    Vector("rv64-logical", "riscv64", ["AND x1,x2,x3", "OR x4,x2,x3", "XOR x5,x2,x3"],
           {"x2": 0xF0, "x3": 0x3C},
           expected_regs={"x1": 0x30, "x4": 0xFC, "x5": 0xCC}, expected_pc=12),
    Vector("rv64-load-store", "riscv64", ["LW x1,0(x2)", "SW x1,8(x2)"],
           {"x2": 0x100}, init_memory={0x100: (0x11223344, 4)},
           expected_regs={"x1": 0x11223344}, expected_memory={0x108: (0x11223344, 4)}, expected_pc=8),
    Vector("rv64-beq-taken", "riscv64", ["BEQ x1,x2,4", "ADDI x3,x0,1", "ADDI x4,x0,2"],
           {"x1": 5, "x2": 5}, expected_regs={"x3": 0, "x4": 2}, expected_pc=12),
    Vector("rv64-beq-not-taken", "riscv64", ["BEQ x1,x2,8", "ADDI x3,x0,1", "ADDI x4,x0,2"],
           {"x1": 5, "x2": 6}, expected_regs={"x3": 1, "x4": 2}, expected_pc=12),
    Vector("rv64-jal-link", "riscv64", ["JAL x1,4", "ADDI x2,x0,1", "ADDI x3,x0,2"],
           expected_regs={"x1": 4, "x2": 0, "x3": 2}, expected_pc=12),
    Vector("rv64-lui-upper", "riscv64", ["LUI x1,0x1"],
           expected_regs={"x1": 0x1000}, expected_pc=4),
    Vector("rv64-ecall-trap", "riscv64", ["ECALL"],
           expected_trap="ECALL", expected_pc=4),
]

ILLEGAL: list[tuple[str, str, bytes]] = [
    ("x86-64", "push-es-invalid-in-64-bit", bytes.fromhex("06")),
    ("x86-64", "pusha-invalid-in-64-bit", bytes.fromhex("60")),
    ("x86-64", "truncated-rex", bytes.fromhex("48")),
    ("x86-64", "missing-modrm", bytes.fromhex("488b")),
    ("aarch64", "all-zero-reserved", bytes.fromhex("00000000")),
    ("aarch64", "all-ones-reserved", bytes.fromhex("ffffffff")),
    ("aarch64", "truncated-word", bytes.fromhex("00")),
    ("riscv64", "zero-word-illegal", bytes.fromhex("00000000")),
    ("riscv64", "reserved-opcode-0x2f", bytes.fromhex("2f00000f")),
    ("riscv64", "reserved-r-type-funct7", bytes.fromhex("33000002")),
    ("riscv64", "reserved-opcode-0x1f", bytes.fromhex("1f00000f")),
    ("riscv64", "truncated-word", bytes.fromhex("00")),
]

EMULATOR_WORDS = [
    "ADD x1,x2,x3", "SUB x1,x2,x3", "AND x1,x2,x3", "OR x1,x2,x3",
    "XOR x1,x2,x3", "ADDI x1,x2,5", "ANDI x1,x2,1", "ORI x1,x2,2",
    "XORI x1,x2,3", "SLTI x1,x2,1", "LW x1,8(x2)", "SW x3,8(x2)",
    "BEQ x1,x2,8", "JAL x1,8", "LUI x1,0x1", "AUIPC x1,0x1",
]


def set_reg(state: State, arch: str, name: str, value: int) -> None:
    index = REG_ALIASES[arch][name]
    mask = (1 << 64) - 1
    state.regs[index] = value & mask


def reg_value(state: State, arch: str, name: str) -> int:
    return state.regs[REG_ALIASES[arch][name]]


def load_reference_codec() -> Any:
    path = ROOT / "tools" / "isa" / "riscv_codec.py"
    spec = importlib.util.spec_from_file_location("chimera_reference_riscv_codec", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load tools/isa/riscv_codec.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_program(arch: str, lines: list[str], state: State, max_steps: int = 32) -> tuple[State, int, int]:
    decoded = [assemble(arch, line) for line in lines]
    offsets: list[int] = []
    blob = bytearray()
    for item in decoded:
        offsets.append(len(blob))
        blob.extend(item.data)
    state.memory[0:len(blob)] = blob
    by_pc = dict(zip(offsets, decoded))
    steps = 0
    while state.pc in by_pc and steps < max_steps and not state.halted:
        step(arch, by_pc[state.pc], state)
        steps += 1
    return state, steps, len(blob)


def check_case(vec: Vector) -> dict[str, Any]:
    case: dict[str, Any] = {"name": vec.name, "arch": vec.arch, "lines": vec.lines}
    try:
        state = State.zeros(16 if vec.arch == "x86-64" else 32, 8192)
        for name, value in vec.init_regs.items():
            set_reg(state, vec.arch, name, value)
        state.flags.update(vec.init_flags)
        for address, (value, width) in vec.init_memory.items():
            state.write_mem(address, width, value)
        state, steps, size = run_program(vec.arch, vec.lines, state)
        mismatches: list[str] = []
        for name, expected in vec.expected_regs.items():
            actual = reg_value(state, vec.arch, name)
            if actual != (expected & ((1 << 64) - 1)):
                mismatches.append(f"{name}: expected 0x{expected & ((1 << 64) - 1):x}, got 0x{actual:x}")
        for name, expected in vec.expected_flags.items():
            if state.flags.get(name) != expected:
                mismatches.append(f"flag {name}: expected {expected}, got {state.flags.get(name)}")
        for address, (expected, width) in vec.expected_memory.items():
            actual = state.read_mem(address, width)
            if actual != (expected & ((1 << (8 * width)) - 1)):
                mismatches.append(f"mem[0x{address:x}]: expected 0x{expected:x}, got 0x{actual:x}")
        if vec.expected_pc is not None and state.pc != vec.expected_pc:
            mismatches.append(f"pc: expected 0x{vec.expected_pc:x}, got 0x{state.pc:x}")
        if vec.expected_trap != state.trap:
            mismatches.append(f"trap: expected {vec.expected_trap!r}, got {state.trap!r}")
        case.update({"passed": not mismatches, "steps": steps, "program_bytes": size,
                     "final_registers": {name: reg_value(state, vec.arch, name) for name in vec.expected_regs},
                     "final_flags": dict(state.flags), "final_pc": state.pc, "trap": state.trap,
                     "mismatches": mismatches})
    except Exception as exc:
        case.update({"passed": False, "error": f"{type(exc).__name__}: {exc}"})
    return case


def run() -> dict[str, Any]:
    universal = json.loads(UNIVERSAL.read_text(encoding="utf-8"))
    native_catalog = json.loads(NATIVE_CATALOG.read_text(encoding="utf-8"))
    results: dict[str, list[dict[str, Any]]] = {
        "roundtrip": [], "execution": [], "illegal": [], "emulator": [], "object": []
    }

    for (arch, mnemonic, form), text in sorted(CATALOG_VECTORS.items()):
        case: dict[str, Any] = {"arch": arch, "mnemonic": mnemonic, "form": form, "text": text}
        try:
            row = next(r for r in universal["instructions"] if r["architecture"] == arch
                       and r["mnemonic"] == mnemonic and r["form_id"] == form)
            decoded = assemble(arch, text)
            back = disassemble(arch, decoded.data)
            order = "big" if arch == "x86-64" else "little"
            word = int.from_bytes(decoded.data, order)
            mask, value = int(row["mask_bits"], 2), int(row["value_bits"], 2)
            fixed_ok = (word & mask) == (value & mask)
            roundtrip_ok = back.text == decoded.text
            case.update({"passed": fixed_ok and roundtrip_ok, "bytes": decoded.data.hex(),
                         "disassembled": back.text, "fixed_mask_match": fixed_ok,
                         "roundtrip_match": roundtrip_ok,
                         "effects": effects(arch, decoded)})
        except Exception as exc:
            case.update({"passed": False, "error": f"{type(exc).__name__}: {exc}"})
        results["roundtrip"].append(case)

    for vec in VECTORS:
        results["execution"].append(check_case(vec))

    for arch, name, blob in ILLEGAL:
        case = {"arch": arch, "name": name, "bytes": blob.hex()}
        try:
            disassemble(arch, blob)
            case["passed"] = False
            case["error"] = "decoder accepted an illegal encoding"
        except IllegalInstruction as exc:
            case["passed"] = True
            case["reason"] = str(exc)
        except Exception as exc:
            case["passed"] = False
            case["error"] = f"wrong exception: {type(exc).__name__}: {exc}"
        results["illegal"].append(case)

    reference = load_reference_codec()
    for text in EMULATOR_WORDS:
        case = {"kind": "encoding", "text": text}
        try:
            ours = assemble("riscv64", text)
            theirs = reference.encode(text)
            case.update({"passed": ours.data == theirs.to_bytes(4, "little"),
                         "ours": ours.data.hex(), "reference": f"0x{theirs:08x}"})
        except Exception as exc:
            case.update({"passed": False, "error": f"{type(exc).__name__}: {exc}"})
        results["emulator"].append(case)
    # Seed x2 with a nonzero value through an actual instruction so both models
    # start from reset state yet exercise a non-trivial data path.
    program = ["ADDI x2,x0,7", "ADDI x1,x2,5", "ADD x1,x1,x2"]
    ours_state, _, _ = run_program("riscv64", program, State.zeros(32, 8192))
    reference_words = [reference.encode(line) for line in program]
    ref_result = reference.execute(reference_words)
    case = {"kind": "execution", "program": program,
            "passed": (ours_state.regs[1] & 0xFFFFFFFF) == (ref_result["registers"][1] & 0xFFFFFFFF)}
    case.update({"ours_r1_low32": ours_state.regs[1] & 0xFFFFFFFF,
                 "reference_r1_low32": ref_result["registers"][1] & 0xFFFFFFFF,
                 "note": "Reference model is RV32I; comparison is restricted to low 32 bits of the shared base subset."})
    results["emulator"].append(case)

    arch_names = [a["id"] for a in native_catalog["architectures"]]
    for arch in sorted({"x86-64", "aarch64", "riscv64", "chimera-c8192"}):
        case = {"arch": arch, "kind": "valid-object"}
        try:
            if arch == "chimera-c8192":
                # No real backend exists for this inventory entry: emit a valid
                # empty object only. This is container validation, not an ISA claim.
                text = Section(".text", SECTION_TYPES["PROGBITS"], PERM_READ | PERM_EXEC, 4, 0x1000, b"", 0)
                strtab = Section(".strtab", SECTION_TYPES["STRTAB"], PERM_READ, 1, 0, b"", 0)
                blob = build_object(arch, [Section("", SECTION_TYPES["NULL"], 0, 1, 0, b"", 0), text, strtab],
                                    [Symbol("", 0, 0, 0, 0, 0)], [])
            else:
                blob = demo_object(arch, "ADDI x1,x2,5" if arch == "riscv64" else
                                   "ADD X0,X1,X2" if arch == "aarch64" else "ADD [RAX],RAX")
            obj = validate_object(blob, expected_arch=arch, arch_names=arch_names)
            case.update({"passed": len(obj.sections) >= 3 and bool(obj.symbols),
                         "sections": [s.name for s in obj.sections],
                         "symbols": [s.name for s in obj.symbols],
                         "relocations": len(obj.relocations)})
        except Exception as exc:
            case.update({"passed": False, "error": f"{type(exc).__name__}: {exc}"})
        results["object"].append(case)
    valid = demo_object("riscv64")
    body = valid[:-32]

    def reseal(mutated: bytes) -> bytes:
        return mutated + hashlib.sha256(mutated).digest()

    def flip_arch(mutated: bytes) -> bytes:
        return mutated[:16] + (int.from_bytes(mutated[16:18], "little") ^ 0x5A5A).to_bytes(2, "little") + mutated[18:]

    def bad_section_align(mutated: bytes) -> bytes:
        # Section 1 record begins at offset 64; its align byte is at 64+40+6.
        at = 64 + SECTION_STRUCT.size + 6  # section 1 align byte
        return mutated[:at] + bytes([3]) + mutated[at + 1:]

    def bad_reloc_offset(mutated: bytes) -> bytes:
        # Relocation table starts at the header's reloc_off field (offset 34).
        at = int.from_bytes(mutated[34:38], "little")
        return mutated[:at + 16] + (0xFFFF).to_bytes(8, "little") + mutated[at + 24:]

    mutations = {
        "bad-magic": lambda b: reseal(b"\0" + b[1:]),
        "bad-version": lambda b: reseal(b[:8] + (2).to_bytes(2, "little") + b[10:]),
        "bad-digest": lambda b: b[:-1] + bytes([b[-1] ^ 1]),
        "truncated": lambda b: b[:-1],
        "bad-arch-id": lambda b: reseal(flip_arch(b)),
        "bad-section-align": lambda b: reseal(bad_section_align(b)),
        "bad-reloc-offset": lambda b: reseal(bad_reloc_offset(b)),
    }
    for name, mutate in mutations.items():
        case = {"kind": "malformed-object", "name": name}
        try:
            validate_object(mutate(body), arch_names=arch_names)
            case.update({"passed": False, "error": "validator accepted a malformed object"})
        except ObjectFormatError as exc:
            case.update({"passed": True, "reason": str(exc)})
        except Exception as exc:
            case.update({"passed": False, "error": f"wrong exception: {type(exc).__name__}: {exc}"})
        results["object"].append(case)

    counts = {category: {"total": len(cases), "passed": sum(bool(c.get("passed")) for c in cases),
                         "failed": sum(not c.get("passed") for c in cases)}
              for category, cases in results.items()}
    total = sum(c["total"] for c in counts.values())
    passed = sum(c["passed"] for c in counts.values())
    evidence = {
        "schema": "CHM-ISA-NATIVE-CONFORMANCE-EVIDENCE-1",
        "status": "partial-engineering-evidence-only",
        "disclaimer": (
            "This is a bounded vertical-slice run, not full catalogue conformance. Official counts are copied "
            "unchanged from the universal catalogue and are not upgraded by these engineering checks."
        ),
        "official_catalog": {"path": UNIVERSAL.relative_to(ROOT).as_posix(),
                             "record_count": universal["record_count"], "coverage": universal["coverage"]},
        "derived_catalog": {
            "path": NATIVE_CATALOG.relative_to(ROOT).as_posix(),
            "architecture_inventory_count": native_catalog["inventory"]["architecture_inventory_count"],
            "instruction_record_count": native_catalog["inventory"]["instruction_record_count"],
            "real_backend_instruction_rows": native_catalog["inventory"]["real_backend_instruction_rows"],
            "descriptors_only_or_not_implemented_instruction_rows":
                native_catalog["inventory"]["descriptors_only_or_not_implemented_instruction_rows"],
        },
        "counts": counts,
        "total_checks": total, "passed_checks": passed, "failed_checks": total - passed,
        "results": results,
    }
    if universal["coverage"]["conformance_tested"] != 0 or universal["coverage"]["not_implemented"] != 1613:
        evidence["baseline_error"] = "official baseline changed; investigate before trusting results"
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strict", action="store_true", help="exit nonzero if any engineering check fails")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    evidence = run()
    payload = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    if not args.no_write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"wrote {args.output}")
    print(json.dumps({"status": evidence["status"], "counts": evidence["counts"],
                      "total_checks": evidence["total_checks"], "passed_checks": evidence["passed_checks"],
                      "failed_checks": evidence["failed_checks"],
                      "official": evidence["official_catalog"]["coverage"]}, indent=2))
    if "baseline_error" in evidence:
        print("ERROR: official baseline changed", file=sys.stderr)
        return 2
    if args.strict and evidence["failed_checks"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
