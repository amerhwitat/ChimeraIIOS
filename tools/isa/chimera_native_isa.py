#!/usr/bin/env python3
"""Chimera native CISC/RISC instruction formats and versioned object format.

This module implements a deliberately bounded but REAL vertical slice:

  * x86-64 CISC     : REX + opcode + ModRM/SIB/displacement/imm, register-direct
                      and base/index memory addressing, branches, stack ops.
  * AArch64 RISC    : fixed 32-bit fielded data processing, loads/stores,
                      branches and system instructions.
  * RV64I RISC      : fixed 32-bit R/I/S/B/U/J/system formats, 64-bit semantics.
  * Chimera object  : CHMOBJ1 container with sections, symbols, relocations,
                      permission flags, ABI version, digest and strict loader.

Everything outside the implemented slice stays descriptors-only and is reported
as not-implemented by the catalogue generator. This module never claims official
conformance; test results are engineering evidence only.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1


class IllegalInstruction(ValueError):
    """Raised for an encoding that the implemented decoder must reject."""


class ObjectFormatError(ValueError):
    """Raised for a malformed Chimera native object."""


def sx(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def parse_int(text: str) -> int:
    return int(str(text).strip(), 0)


def u64(value: int) -> int:
    return value & MASK64


@dataclass
class Decoded:
    arch: str
    mnemonic: str
    form: str
    operands: dict[str, Any]
    text: str
    data: bytes
    fields: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "arch": self.arch, "mnemonic": self.mnemonic, "form": self.form,
            "operands": self.operands, "text": self.text,
            "bytes": self.data.hex(), "fields": self.fields,
        }


@dataclass
class State:
    """Tiny architectural state used by the executable conformance vectors."""
    regs: list[int]
    flags: dict[str, int] = field(default_factory=dict)
    memory: bytearray = field(default_factory=lambda: bytearray(4096))
    pc: int = 0
    halted: bool = False
    trap: str | None = None

    @classmethod
    def zeros(cls, count: int, memory: int = 4096) -> "State":
        return cls(regs=[0] * count, memory=bytearray(memory))

    def read_mem(self, address: int, size: int) -> int:
        if address < 0 or address + size > len(self.memory):
            raise IllegalInstruction(f"memory access outside model: 0x{address:x}")
        return int.from_bytes(self.memory[address:address + size], "little")

    def write_mem(self, address: int, size: int, value: int) -> None:
        if address < 0 or address + size > len(self.memory):
            raise IllegalInstruction(f"memory access outside model: 0x{address:x}")
        self.memory[address:address + size] = (value & ((1 << (size * 8)) - 1)).to_bytes(size, "little")


# ---------------------------------------------------------------------------
# x86-64 CISC: REX prefix, opcode, ModRM, optional SIB, displacement, immediate
# ---------------------------------------------------------------------------

X86_REG = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi"] + [f"r{n}" for n in range(8, 16)]
X86_OPCODES = {
    "ADD": 0x01, "OR": 0x09, "AND": 0x21, "SUB": 0x29,
    "XOR": 0x31, "CMP": 0x39, "MOV_TO_MEM": 0x89, "MOV_FROM_MEM": 0x8B,
}
X86_LOGIC = {"AND", "OR", "XOR"}
X86_ARITH = {"ADD", "SUB", "CMP"}


def _x86_reg(token: str) -> int:
    name = token.strip().lower()
    if name.startswith("%"):
        name = name[1:]
    if name not in X86_REG:
        raise ValueError(f"unsupported x86-64 64-bit register: {token}")
    return X86_REG.index(name)


def _x86_reg_text(index: int) -> str:
    return X86_REG[index].upper()


def _x86_split_operands(line: str, count: int) -> list[str]:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != count:
        raise ValueError(f"expected {count} operands, got {len(parts)}")
    return parts


def _x86_parse_mem(text: str) -> dict[str, Any]:
    raw = text.strip()
    if not (raw.startswith("[") and raw.endswith("]")):
        raise ValueError(f"expected memory operand [base+index*scale+disp], got {text}")
    body = raw[1:-1].strip()
    if not body:
        raise ValueError("empty memory operand")
    tokens = re.split(r"([+-])", body)
    if tokens[0] == "":
        tokens = tokens[1:]
    sign = 1
    base: int | None = None
    index: int | None = None
    scale = 1
    disp = 0
    i = 0
    while i < len(tokens):
        token = tokens[i].strip()
        if token in ("+", "-"):
            sign = 1 if token == "+" else -1
            i += 1
            continue
        if not token:
            i += 1
            continue
        if "*" in token:
            reg_part, scale_part = token.split("*", 1)
            if index is not None:
                raise ValueError("only one index register is supported")
            index = _x86_reg(reg_part)
            scale = parse_int(scale_part)
            if scale not in (1, 2, 4, 8):
                raise ValueError("x86 scale must be 1, 2, 4 or 8")
        elif token.lower() in X86_REG:
            if base is not None:
                raise ValueError("only one base register is supported")
            base = _x86_reg(token)
        else:
            disp += sign * parse_int(token)
        i += 1
    return {"kind": "mem", "base": base, "index": index, "scale": scale, "disp": disp}


def _x86_parse_operand(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("["):
        return _x86_parse_mem(text)
    return {"kind": "reg", "index": _x86_reg(text)}


def _x86_mem_text(mem: dict[str, Any]) -> str:
    parts: list[str] = []
    if mem["base"] is not None:
        parts.append(_x86_reg_text(mem["base"]))
    if mem["index"] is not None:
        factor = "" if mem["scale"] == 1 else f"*{mem['scale']}"
        parts.append(f"{_x86_reg_text(mem['index'])}{factor}")
    disp = mem["disp"]
    if disp < 0:
        parts.append(f"-0x{-disp:x}")
    elif disp > 0 or not parts:
        parts.append(f"0x{disp:x}")
    return "[" + "+".join(parts) + "]"


def _x86_operand_text(op: dict[str, Any]) -> str:
    return _x86_mem_text(op) if op["kind"] == "mem" else _x86_reg_text(op["index"])


def _x86_modrm(rm: dict[str, Any], reg_index: int) -> tuple[int, bytes, int, int]:
    """Return ModRM byte, SIB+displacement bytes, REX.X and REX.B bits."""
    if rm["kind"] == "reg":
        return 0xC0 | ((reg_index & 7) << 3) | (rm["index"] & 7), b"", 0, rm["index"] >> 3
    base, index, scale, disp = rm["base"], rm["index"], rm["scale"], rm["disp"]
    rex_x = (index >> 3) if index is not None else 0
    rex_b = (base >> 3) if base is not None else 0
    if base is None:
        if index is not None:
            raise ValueError("index-only x86 addressing requires a base in this slice")
        return (reg_index & 7) << 3 | 5, struct.pack("<i", disp), 0, 0
    base_low = base & 7
    need_sib = base_low == 4 or index is not None
    if disp == 0 and base_low != 5:
        mod = 0
        disp_bytes = b""
    elif -128 <= disp <= 127:
        mod = 1
        disp_bytes = struct.pack("<b", disp)
    else:
        mod = 2
        disp_bytes = struct.pack("<i", disp)
    rm_low = 4 if need_sib else base_low
    modrm = (mod << 6) | ((reg_index & 7) << 3) | rm_low
    trailer = b""
    if need_sib:
        scale_bits = {1: 0, 2: 1, 4: 2, 8: 3}[scale]
        index_low = 4 if index is None else (index & 7)
        sib = (scale_bits << 6) | (index_low << 3) | base_low
        trailer += bytes([sib])
    trailer += disp_bytes
    return modrm, trailer, rex_x, rex_b


def _x86_decode_rm(modrm: int, sib: int | None, disp: int, rex_x: int, rex_b: int) -> tuple[dict[str, Any], int]:
    mod = modrm >> 6
    reg = (modrm >> 3) & 7  # REX.R is applied by the caller
    rm_low = modrm & 7
    if mod == 3:
        return {"kind": "reg", "index": rm_low | (rex_b << 3)}, reg
    if rm_low == 4:
        if sib is None:
            raise IllegalInstruction("ModRM rm=4 without SIB")
        scale = 1 << (sib >> 6)
        index_low = (sib >> 3) & 7
        base_low = sib & 7
        index = None if index_low == 4 and not rex_x else index_low | (rex_x << 3)
        base = base_low | (rex_b << 3)
        return {"kind": "mem", "base": base, "index": index, "scale": scale, "disp": disp}, reg
    if rm_low == 5 and mod == 0:
        return {"kind": "mem", "base": None, "index": None, "scale": 1, "disp": disp}, reg
    return {"kind": "mem", "base": rm_low | (rex_b << 3), "index": None, "scale": 1, "disp": disp}, reg


X86_DESCRIPTORS = {
    ("ADD", "rm64_r64"): {"opcode": 0x01, "flags": ("arith",)},
    ("OR", "rm64_r64"): {"opcode": 0x09, "flags": ("logic",)},
    ("AND", "rm64_r64"): {"opcode": 0x21, "flags": ("logic",)},
    ("SUB", "rm64_r64"): {"opcode": 0x29, "flags": ("arith",)},
    ("XOR", "rm64_r64"): {"opcode": 0x31, "flags": ("logic",)},
    ("CMP", "rm64_r64"): {"opcode": 0x39, "flags": ("compare",)},
    ("MOV", "rm64_r64"): {"opcode": 0x89, "flags": ("store",)},
    ("MOV", "r64_rm64"): {"opcode": 0x8B, "flags": ("load",)},
    ("NOP", "fixed"): {"opcode": 0x90, "flags": ("nop",)},
    ("RET", "fixed"): {"opcode": 0xC3, "flags": ("ret",)},
    ("PUSH", "r64"): {"opcode": 0x50, "flags": ("push",)},
    ("POP", "r64"): {"opcode": 0x58, "flags": ("pop",)},
    ("JMP", "rel32"): {"opcode": 0xE9, "flags": ("jmp",)},
    ("CALL", "rel32"): {"opcode": 0xE8, "flags": ("call",)},
}


class X86Backend:
    arch = "x86-64"
    family = "CISC x86-64"
    endian = "little"

    def formats(self) -> dict[tuple[str, str], dict[str, Any]]:
        out = {}
        for (mnemonic, form), spec in X86_DESCRIPTORS.items():
            out[(mnemonic, form)] = {
                "format_class": "REX.W+opcode+ModRM/SIB+disp+imm",
                "opcode": f"0x{spec['opcode']:02X}",
                "prefixes": ["REX.W mandatory for these 64-bit forms", "REX.R/X/B encode register extensions"],
                "bit_fields": [
                    {"name": "REX", "bits": "7:0", "role": "prefix", "value": "0x48|R<<2|X<<1|B"},
                    {"name": "opcode", "bits": "7:0", "role": "opcode"},
                    {"name": "ModRM.mod", "bits": "7:6", "role": "addressing mode"},
                    {"name": "ModRM.reg", "bits": "5:3", "role": "register operand / opcode extension"},
                    {"name": "ModRM.rm", "bits": "2:0", "role": "base or register operand"},
                    {"name": "SIB", "bits": "7:0", "role": "index/scale/base", "optional": True},
                    {"name": "displacement", "bits": "8 or 32", "role": "address", "optional": True},
                    {"name": "imm32/imm64", "bits": "32 or 64", "role": "immediate", "optional": True},
                ],
                "semantic_class": spec["flags"][0],
            }
        return out

    def assemble(self, line: str) -> Decoded:
        text = line.split("#", 1)[0].strip()
        if not text:
            raise ValueError("empty instruction")
        parts = text.replace(",", " ").split()
        mnemonic = parts[0].upper()
        rest = parts[1:]
        if mnemonic in ("NOP", "RET") and not rest:
            form = "fixed"
            spec = X86_DESCRIPTORS[(mnemonic, form)]
            data = bytes([spec["opcode"]])
            return Decoded(self.arch, mnemonic, form, {}, f"{mnemonic}", data)
        if mnemonic in ("PUSH", "POP") and len(rest) == 1:
            form = "r64"
            reg = _x86_reg(rest[0])
            prefix = bytes([0x41]) if reg >= 8 else b""
            data = prefix + bytes([X86_DESCRIPTORS[(mnemonic, form)]["opcode"] + (reg & 7)])
            op = {"kind": "reg", "index": reg}
            return Decoded(self.arch, mnemonic, form, {"reg": op}, f"{mnemonic} {_x86_operand_text(op)}", data)
        if mnemonic in ("JMP", "CALL") and len(rest) == 1:
            form = "rel32"
            rel = parse_int(rest[0])
            if not -(1 << 31) <= rel < (1 << 31):
                raise ValueError("rel32 out of range")
            data = bytes([X86_DESCRIPTORS[(mnemonic, form)]["opcode"]]) + struct.pack("<i", rel)
            return Decoded(self.arch, mnemonic, form, {"rel": rel}, f"{mnemonic} 0x{rel & MASK32:x}", data)
        if (mnemonic, "rm64_r64") in X86_DESCRIPTORS and len(rest) == 2:
            form = "rm64_r64"
            dst = _x86_parse_operand(rest[0])
            src = _x86_parse_operand(rest[1])
            if dst["kind"] == "mem" and src["kind"] == "mem":
                raise ValueError("x86 cannot encode mem,mem in this form")
            if (mnemonic, "r64_rm64") in X86_DESCRIPTORS and dst["kind"] == "reg" and src["kind"] == "mem":
                form = "r64_rm64"
                reg_op, rm_op = dst, src
            else:
                reg_op, rm_op = src, dst
                if reg_op["kind"] != "reg":
                    raise ValueError(f"{mnemonic} requires a register operand")
            spec = X86_DESCRIPTORS[(mnemonic, form)]
            modrm, trailer, rex_x, rex_b = _x86_modrm(rm_op, reg_op["index"])
            rex = 0x48 | ((reg_op["index"] >> 3) << 2) | (rex_x << 1) | rex_b
            data = bytes([rex, spec["opcode"], modrm]) + trailer
            canonical = f"{mnemonic} {_x86_operand_text(dst)}, {_x86_operand_text(src)}"
            return Decoded(self.arch, mnemonic, form, {"dst": dst, "src": src}, canonical, data)
        raise ValueError(f"unsupported x86-64 slice instruction: {text}")

    def disassemble(self, data: bytes) -> Decoded:
        if not data:
            raise IllegalInstruction("empty x86-64 instruction")
        pos = 0
        rex = 0
        if 0x40 <= data[0] <= 0x4F:
            rex = data[pos]
            pos += 1
        if pos >= len(data):
            raise IllegalInstruction("truncated REX prefix")
        opcode = data[pos]
        pos += 1
        rex_r = (rex >> 2) & 1
        rex_x = (rex >> 1) & 1
        rex_b = rex & 1
        if opcode in (0x90, 0xC3):
            if pos != len(data):
                raise IllegalInstruction("trailing bytes after fixed instruction")
            name = "NOP" if opcode == 0x90 else "RET"
            return Decoded(self.arch, name, "fixed", {}, name, data[:pos])
        if opcode in (0x50, 0x58):
            if rex != 0 and rex != 0x41:
                raise IllegalInstruction("unsupported REX prefix on push/pop")
            if pos != len(data):
                raise IllegalInstruction("trailing bytes after push/pop")
            name = "PUSH" if opcode == 0x50 else "POP"
            reg = {"kind": "reg", "index": (opcode & 7) | ((rex & 1) << 3)}
            return Decoded(self.arch, name, "r64", {"reg": reg}, f"{name} {_x86_operand_text(reg)}", data[:pos])
        if opcode in (0xE8, 0xE9):
            if len(data) - pos != 4:
                raise IllegalInstruction("truncated rel32")
            rel = struct.unpack_from("<i", data, pos)[0]
            name = "CALL" if opcode == 0xE8 else "JMP"
            return Decoded(self.arch, name, "rel32", {"rel": rel}, f"{name} 0x{rel & MASK32:x}", data[:pos + 4])
        reverse = {v["opcode"]: (k, v) for k, v in X86_DESCRIPTORS.items()}
        if opcode not in reverse:
            raise IllegalInstruction(f"unimplemented or illegal x86-64 opcode 0x{opcode:02x}")
        (mnemonic, form), spec = reverse[opcode]
        if form == "fixed" or form in ("r64", "rel32"):
            raise IllegalInstruction("opcode overlap in decoder table")
        if not rex & 8:
            raise IllegalInstruction("REX.W is mandatory for ModRM 64-bit forms")
        if pos >= len(data):
            raise IllegalInstruction("missing ModRM byte")
        modrm = data[pos]
        pos += 1
        mod = modrm >> 6
        sib: int | None = None
        disp = 0
        if mod != 3 and (modrm & 7) == 4:
            if pos >= len(data):
                raise IllegalInstruction("missing SIB byte")
            sib = data[pos]
            pos += 1
        if mod == 1:
            if pos >= len(data):
                raise IllegalInstruction("missing disp8")
            disp = sx(data[pos], 8)
            pos += 1
        elif mod == 2:
            if len(data) - pos < 4:
                raise IllegalInstruction("missing disp32")
            disp = struct.unpack_from("<i", data, pos)[0]
            pos += 4
        elif mod == 0 and (modrm & 7) == 5 and sib is None:
            if len(data) - pos < 4:
                raise IllegalInstruction("missing disp32 address")
            disp = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        reg_index = (((modrm >> 3) & 7) | (rex_r << 3))
        rm, _ = _x86_decode_rm(modrm, sib, disp, rex_x, rex_b)
        if mod == 3 and rm["kind"] != "reg":
            raise IllegalInstruction("invalid ModRM register form")
        reg_op = {"kind": "reg", "index": reg_index}
        if form == "r64_rm64":
            dst, src = reg_op, rm
        else:
            dst, src = rm, reg_op
        canonical = f"{mnemonic} {_x86_operand_text(dst)}, {_x86_operand_text(src)}"
        return Decoded(self.arch, mnemonic, form, {"dst": dst, "src": src}, canonical, data[:pos],
                       {"rex": rex, "opcode": opcode, "modrm": modrm, "sib": sib if sib is not None else 0, "disp": disp})

    def _effective_address(self, mem: dict[str, Any], state: State) -> int:
        address = mem["disp"]
        if mem["base"] is not None:
            address += state.regs[mem["base"]]
        if mem["index"] is not None:
            address += state.regs[mem["index"]] * mem["scale"]
        return u64(address)

    def _read_operand(self, op: dict[str, Any], state: State) -> int:
        if op["kind"] == "reg":
            return state.regs[op["index"]]
        return state.read_mem(self._effective_address(op, state), 8)

    def _write_operand(self, op: dict[str, Any], state: State, value: int) -> None:
        if op["kind"] == "reg":
            if op["index"] != 0 or True:  # x86 has no hardwired zero register
                state.regs[op["index"]] = u64(value)
        else:
            state.write_mem(self._effective_address(op, state), 8, value)

    @staticmethod
    def _set_flags(state: State, result: int, lhs: int, rhs: int, kind: str) -> None:
        result &= MASK64
        state.flags["ZF"] = int(result == 0)
        state.flags["SF"] = int(bool(result >> 63))
        parity = bin(result & 0xFF).count("1") % 2
        state.flags["PF"] = int(parity == 0)
        if kind in ("arith", "compare"):
            if kind == "arith":
                state.flags["CF"] = int(lhs + rhs > MASK64)
                state.flags["OF"] = int((~(lhs ^ rhs) & (lhs ^ result) & (1 << 63)) != 0)
            else:
                state.flags["CF"] = int(lhs < rhs)
                state.flags["OF"] = int(((lhs ^ rhs) & (lhs ^ result) & (1 << 63)) != 0)
            state.flags["AF"] = int(((lhs ^ rhs ^ result) & 0x10) != 0)
        else:
            state.flags["CF"] = 0
            state.flags["OF"] = 0
            state.flags["AF"] = 0

    def step(self, decoded: Decoded, state: State) -> None:
        m, ops = decoded.mnemonic, decoded.operands
        spec = X86_DESCRIPTORS[(m, decoded.form)]["flags"][0]
        length = len(decoded.data)
        if spec in ("arith", "compare", "logic", "store", "load"):
            if spec in ("store", "load"):
                value = self._read_operand(ops["src"], state)
                self._write_operand(ops["dst"], state, value)
            else:
                lhs = self._read_operand(ops["src"], state)
                dst = self._read_operand(ops["dst"], state)
                if m == "ADD":
                    value = u64(dst + lhs)
                elif m in ("SUB", "CMP"):
                    value = u64(dst - lhs)
                elif m == "AND":
                    value = dst & lhs
                elif m == "OR":
                    value = dst | lhs
                elif m == "XOR":
                    value = dst ^ lhs
                else:
                    raise IllegalInstruction(f"no x86-64 semantics for {m}")
                # SUB/CMP both use subtraction flag rules; CMP discards the result.
                flag_kind = "compare" if m in ("SUB", "CMP") else spec
                self._set_flags(state, value, dst, lhs, flag_kind)
                if spec in ("arith", "logic"):
                    self._write_operand(ops["dst"], state, value)
            state.pc = u64(state.pc + length)
        elif spec == "push":
            state.regs[4] = u64(state.regs[4] - 8)
            state.write_mem(state.regs[4], 8, state.regs[ops["reg"]["index"]])
            state.pc = u64(state.pc + length)
        elif spec == "pop":
            value = state.read_mem(state.regs[4], 8)
            state.regs[ops["reg"]["index"]] = u64(value)
            state.regs[4] = u64(state.regs[4] + 8)
            state.pc = u64(state.pc + length)
        elif spec == "jmp":
            state.pc = u64(state.pc + length + ops["rel"])
        elif spec == "call":
            ret = u64(state.pc + length)
            state.regs[4] = u64(state.regs[4] - 8)
            state.write_mem(state.regs[4], 8, ret)
            state.pc = u64(ret + ops["rel"])
        elif spec == "ret":
            state.pc = u64(state.read_mem(state.regs[4], 8))
            state.regs[4] = u64(state.regs[4] + 8)
        else:
            state.pc = u64(state.pc + length)

    def effects(self, decoded: Decoded) -> dict[str, Any]:
        m, ops = decoded.mnemonic, decoded.operands
        spec = X86_DESCRIPTORS[(m, decoded.form)]["flags"][0]
        reads: list[str] = []
        writes: list[str] = []
        memory = "none"

        def registers(op: dict[str, Any]) -> list[str]:
            if op["kind"] == "reg":
                return [_x86_reg_text(op["index"])]
            names = []
            if op.get("base") is not None:
                names.append(_x86_reg_text(op["base"]))
            if op.get("index") is not None:
                names.append(_x86_reg_text(op["index"]))
            return names

        if spec in ("arith", "compare", "logic", "store", "load"):
            dst, src = ops["dst"], ops["src"]
            if spec == "store":
                reads += registers(src) + registers(dst)  # value plus base/index address
                memory = "write"
            elif spec == "load":
                reads += registers(src)
                writes += registers(dst) if dst["kind"] == "reg" else []
                memory = "read"
            else:
                reads += registers(dst) + registers(src)
                if spec in ("arith", "logic") and dst["kind"] == "reg":
                    writes += registers(dst)
                if dst["kind"] == "mem":
                    memory = "read-modify-write" if spec == "arith" else "read"
        elif spec == "push":
            reads += [_x86_reg_text(ops["reg"]["index"]), "RSP"]
            writes += ["RSP"]
            memory = "write stack"
        elif spec == "pop":
            reads += ["RSP"]
            writes += [_x86_reg_text(ops["reg"]["index"]), "RSP"]
            memory = "read stack"
        elif spec == "call":
            reads += ["RSP"]
            writes += ["RSP"]
            memory = "write stack"
        elif spec == "ret":
            reads += ["RSP"]
            writes += ["RSP"]
            memory = "read stack"
        flags = ["CF", "PF", "AF", "ZF", "SF", "OF"] if spec in ("arith", "compare", "logic") else []
        return {
            "registers_read": sorted(set(reads)), "registers_written": sorted(set(writes)),
            "registers_clobbered": [], "flags_read": [], "flags_written": flags,
            "memory_effects": memory,
            "privilege": "user/supervisor (form-dependent)",
        }

# ---------------------------------------------------------------------------
# AArch64 RISC: fixed 32-bit instruction words
# ---------------------------------------------------------------------------

def _a64_reg(token: str) -> int:
    name = token.strip().upper()
    if not re.fullmatch(r"[XW]\d+", name):
        raise ValueError(f"unsupported AArch64 register: {token}")
    index = int(name[1:])
    if index > 30:
        raise ValueError("this slice uses X0..X30 (X31/ZR excluded)")
    return index


def _a64_reg_text(index: int) -> str:
    return f"X{index}"


class AArch64Backend:
    arch = "aarch64"
    family = "RISC aarch64"
    endian = "little"

    def formats(self) -> dict[tuple[str, str], dict[str, Any]]:
        def fields(spec: str) -> list[dict[str, Any]]:
            return [{"name": name, "bits": bits, "role": role} for name, bits, role in spec]
        dp = fields([("sf/op", "31:29", "64-bit opcode class"), ("shift", "23:22", "shift kind (0=LSL)"),
                     ("Rm", "20:16", "source register"), ("imm6", "15:10", "shift amount / immediate"),
                     ("Rn", "9:5", "source register"), ("Rd", "4:0", "destination register")])
        return {
            ("ADD", "rrr"): {"format_class": "A64 data-processing (shifted register)", "opcode": "0x8B000000", "bit_fields": dp,
                             "options": ["LSL shift 0..63"], "semantic_class": "arith"},
            ("SUB", "rrr"): {"format_class": "A64 data-processing (shifted register)", "opcode": "0xCB000000", "bit_fields": dp,
                             "options": ["LSL shift 0..63"], "semantic_class": "arith"},
            ("ADD", "imm"): {"format_class": "A64 add/subtract immediate", "opcode": "0x91000000",
                             "bit_fields": fields([("op", "30:29", "ADD/SUB"), ("imm12", "21:10", "unsigned immediate"),
                                                   ("Rn", "9:5", "source"), ("Rd", "4:0", "destination")]),
                             "options": ["optional 12-bit shift by 12"], "semantic_class": "arith"},
            ("SUB", "imm"): {"format_class": "A64 add/subtract immediate", "opcode": "0xD1000000",
                             "bit_fields": fields([("op", "30:29", "ADD/SUB"), ("imm12", "21:10", "unsigned immediate"),
                                                   ("Rn", "9:5", "source"), ("Rd", "4:0", "destination")]),
                             "options": ["optional 12-bit shift by 12"], "semantic_class": "arith"},
            ("AND", "rrr"): {"format_class": "A64 logical (shifted register)", "opcode": "0x8A000000", "bit_fields": dp,
                             "semantic_class": "logic"},
            ("ORR", "rrr"): {"format_class": "A64 logical (shifted register)", "opcode": "0xAA000000", "bit_fields": dp,
                             "semantic_class": "logic"},
            ("EOR", "rrr"): {"format_class": "A64 logical (shifted register)", "opcode": "0xCA000000", "bit_fields": dp,
                             "semantic_class": "logic"},
            ("LDR", "unsigned"): {"format_class": "A64 load/store unsigned offset", "opcode": "0xF9400000",
                                  "bit_fields": fields([("size/opc", "31:22", "64-bit load"), ("imm12", "21:10", "uimm scaled by 8"),
                                                        ("Rn", "9:5", "base"), ("Rt", "4:0", "target")]),
                                  "options": ["scale=8"], "semantic_class": "load"},
            ("STR", "unsigned"): {"format_class": "A64 load/store unsigned offset", "opcode": "0xF9000000",
                                  "bit_fields": fields([("size/opc", "31:22", "64-bit store"), ("imm12", "21:10", "uimm scaled by 8"),
                                                        ("Rn", "9:5", "base"), ("Rt", "4:0", "source")]),
                                  "options": ["scale=8"], "semantic_class": "store"},
            ("B", "imm"): {"format_class": "A64 unconditional branch immediate", "opcode": "0x14000000",
                           "bit_fields": fields([("op", "31:24", "B/BL"), ("imm26", "25:0", "signed word offset")]),
                           "semantic_class": "branch"},
            ("BL", "imm"): {"format_class": "A64 unconditional branch immediate", "opcode": "0x94000000",
                            "bit_fields": fields([("op", "31:24", "B/BL"), ("imm26", "25:0", "signed word offset")]),
                            "semantic_class": "call"},
            ("BR", "reg"): {"format_class": "A64 branch register", "opcode": "0xD61F0000",
                            "bit_fields": fields([("fixed", "31:5", "BR/BLR/RET"), ("Rn", "9:5", "target register")]),
                            "semantic_class": "branch"},
            ("BLR", "reg"): {"format_class": "A64 branch register", "opcode": "0xD63F0000",
                             "bit_fields": fields([("fixed", "31:5", "BR/BLR/RET"), ("Rn", "9:5", "target register")]),
                             "semantic_class": "call"},
            ("RET", "reg"): {"format_class": "A64 branch register", "opcode": "0xD65F0000",
                             "bit_fields": fields([("fixed", "31:5", "BR/BLR/RET"), ("Rn", "9:5", "return register")]),
                             "semantic_class": "ret"},
            ("NOP", "none"): {"format_class": "A64 hint", "opcode": "0xD503201F", "bit_fields": [],
                              "semantic_class": "nop"},
            ("SVC", "imm"): {"format_class": "A64 exception generation", "opcode": "0xD4000001",
                             "bit_fields": fields([("fixed", "31:16", "SVC"), ("imm16", "20:5", "supervisor call immediate"),
                                                   ("LL", "1:0", "must be 1")]),
                             "semantic_class": "system"},
        }

    def assemble(self, line: str) -> Decoded:
        text = line.split(";", 1)[0].strip()
        parts = text.replace(",", " ").replace("[", " [ ").replace("]", " ").split()
        if not parts:
            raise ValueError("empty instruction")
        m = parts[0].upper()
        a = parts[1:]
        if (m, "none") in self.formats() and not a:
            word = 0xD503201F
            return Decoded(self.arch, m, "none", {}, m, struct.pack("<I", word))
        if (m, "imm") in self.formats() and len(a) == 1:
            if m in ("B", "BL"):
                off = parse_int(a[0])
                if not -(1 << 25) <= off < (1 << 25) or off % 4:
                    raise ValueError("A64 branch offset must be a multiple of 4 within +/-128MiB")
                base = 0x14000000 if m == "B" else 0x94000000
                word = base | ((off // 4) & 0x03FFFFFF)
                return Decoded(self.arch, m, "imm", {"off": off}, f"{m} 0x{off:x}", struct.pack("<I", word))
            if m == "SVC":
                imm = parse_int(a[0].lstrip("#"))
                if not 0 <= imm <= 0xFFFF:
                    raise ValueError("SVC immediate out of range")
                word = 0xD4000001 | (imm << 5)
                return Decoded(self.arch, m, "imm", {"imm": imm}, f"SVC #{imm}", struct.pack("<I", word))
        if (m, "imm") in self.formats() and len(a) == 3 and a[2].startswith("#"):
            rd, rn, imm = _a64_reg(a[0]), _a64_reg(a[1]), parse_int(a[2][1:])
            if not 0 <= imm <= 0xFFF:
                raise ValueError("A64 immediate out of 12-bit range")
            base = 0x91000000 if m == "ADD" else 0xD1000000
            word = base | (imm << 10) | (rn << 5) | rd
            canonical = f"{m} {_a64_reg_text(rd)}, {_a64_reg_text(rn)}, #{imm}"
            return Decoded(self.arch, m, "imm", {"rd": rd, "rn": rn, "imm": imm}, canonical, struct.pack("<I", word))
        lookup = {(mn, fo): sp["opcode"] for (mn, fo), sp in self.formats().items()}
        if (m, "rrr") in lookup and len(a) == 3:
            rd, rn, rm = map(_a64_reg, a)
            if any(x > 30 for x in (rd, rn, rm)):
                raise ValueError("register out of range")
            base = int(lookup[(m, "rrr")], 16)
            word = base | (rm << 16) | (rn << 5) | rd
            canonical = f"{m} {_a64_reg_text(rd)}, {_a64_reg_text(rn)}, {_a64_reg_text(rm)}"
            return Decoded(self.arch, m, "rrr", {"rd": rd, "rn": rn, "rm": rm}, canonical, struct.pack("<I", word))
        if m in ("LDR", "STR") and len(a) == 4 and a[1] == "[":
            rt, rn = _a64_reg(a[0]), _a64_reg(a[2])
            imm = parse_int(a[3].lstrip("#"))
            if imm < 0 or imm > 0xFFF or imm % 8:
                raise ValueError("A64 unsigned offset must be 0..32760 and 8-byte aligned")
            base = int(lookup[(m, "unsigned")], 16)
            word = base | ((imm // 8) << 10) | (rn << 5) | rt
            canonical = f"{m} {_a64_reg_text(rt)}, [{_a64_reg_text(rn)},#{imm}]"
            return Decoded(self.arch, m, "unsigned", {"rt": rt, "rn": rn, "off": imm}, canonical, struct.pack("<I", word))
        if m in ("BR", "BLR", "RET") and len(a) == 1:
            rn = _a64_reg(a[0])
            word = int(lookup[(m, "reg")], 16) | (rn << 5)
            form = "reg" if m != "RET" else "reg"
            canonical = f"{m} {_a64_reg_text(rn)}"
            return Decoded(self.arch, m, form, {"rn": rn}, canonical, struct.pack("<I", word))
        raise ValueError(f"unsupported AArch64 slice instruction: {text}")

    def disassemble(self, data: bytes) -> Decoded:
        if len(data) != 4:
            raise IllegalInstruction("AArch64 instructions are exactly 4 bytes")
        w = struct.unpack("<I", data)[0]
        if w == 0xD503201F:
            return Decoded(self.arch, "NOP", "none", {}, "NOP", data)
        top = w & 0xFF000000
        if top in (0x14000000, 0x94000000):
            off = sx(w & 0x03FFFFFF, 26) * 4
            m = "B" if top == 0x14000000 else "BL"
            return Decoded(self.arch, m, "imm", {"off": off}, f"{m} 0x{off:x}", data, {"word": w})
        if (w & 0xFFE0001F) == 0xD4000001:
            imm = (w >> 5) & 0xFFFF
            return Decoded(self.arch, "SVC", "imm", {"imm": imm}, f"SVC #{imm}", data, {"word": w})
        if (w & 0xFFFFFC1F) in (0xD61F0000, 0xD63F0000, 0xD65F0000):
            m = {0xD61F0000: "BR", 0xD63F0000: "BLR", 0xD65F0000: "RET"}[w & 0xFFFFFC1F]
            rn = (w >> 5) & 31
            return Decoded(self.arch, m, "reg", {"rn": rn}, f"{m} {_a64_reg_text(rn)}", data, {"word": w})
        if (w >> 27) == 0x1F and (w >> 30) == 3:
            opc = (w >> 22) & 3
            if opc not in (0, 1):
                raise IllegalInstruction("unsupported 64-bit load/store opc")
            m = "STR" if opc == 0 else "LDR"
            off = ((w >> 10) & 0xFFF) * 8
            rt, rn = w & 31, (w >> 5) & 31
            return Decoded(self.arch, m, "unsigned", {"rt": rt, "rn": rn, "off": off},
                           f"{m} {_a64_reg_text(rt)}, [{_a64_reg_text(rn)},#{off}]", data, {"word": w})
        if (w >> 24) in (0x91, 0xD1):  # add/subtract immediate, sf=1
            m = "ADD" if (w >> 24) == 0x91 else "SUB"
            imm = (w >> 10) & 0xFFF
            rd, rn = w & 31, (w >> 5) & 31
            return Decoded(self.arch, m, "imm", {"rd": rd, "rn": rn, "imm": imm},
                           f"{m} {_a64_reg_text(rd)}, {_a64_reg_text(rn)}, #{imm}", data, {"word": w})
        if (w >> 24) in (0x8A, 0xAA, 0xCA) and ((w >> 23) & 1) == 0:  # logical shifted register
            opc = (w >> 29) & 3
            names = {0: "AND", 1: "ORR", 2: "EOR"}
            if opc not in names:
                raise IllegalInstruction("ANDS is not part of this slice")
            rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
            if (w >> 21) & 3 or ((w >> 10) & 0x3F):
                raise IllegalInstruction("A64 shift outside implemented LSL #0 slice")
            return Decoded(self.arch, names[opc], "rrr", {"rd": rd, "rn": rn, "rm": rm},
                           f"{names[opc]} {_a64_reg_text(rd)}, {_a64_reg_text(rn)}, {_a64_reg_text(rm)}", data, {"word": w})
        if (w >> 24) in (0x8B, 0xCB):  # add/subtract shifted register
            m = "ADD" if (w >> 24) == 0x8B else "SUB"
            rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
            if ((w >> 22) & 3) or ((w >> 10) & 0x3F):
                raise IllegalInstruction("A64 register shift outside LSL #0 slice")
            return Decoded(self.arch, m, "rrr", {"rd": rd, "rn": rn, "rm": rm},
                           f"{m} {_a64_reg_text(rd)}, {_a64_reg_text(rn)}, {_a64_reg_text(rm)}", data, {"word": w})
        raise IllegalInstruction(f"unimplemented or illegal AArch64 encoding 0x{w:08x}")

    def step(self, decoded: Decoded, state: State) -> None:
        m, o = decoded.mnemonic, decoded.operands
        if m in ("ADD", "SUB") and decoded.form == "imm":
            a = state.regs[o["rn"]]
            value = u64(a + o["imm"]) if m == "ADD" else u64(a - o["imm"])
            state.regs[o["rd"]] = value
            state.pc += 4
        elif m in ("ADD", "SUB") and decoded.form == "rrr":
            a, b = state.regs[o["rn"]], state.regs[o["rm"]]
            state.regs[o["rd"]] = u64(a + b) if m == "ADD" else u64(a - b)
            state.pc += 4
        elif m in ("AND", "ORR", "EOR"):
            a, b = state.regs[o["rn"]], state.regs[o["rm"]]
            state.regs[o["rd"]] = {"AND": a & b, "ORR": a | b, "EOR": a ^ b}[m]
            state.pc += 4
        elif m == "LDR":
            state.regs[o["rt"]] = state.read_mem((state.regs[o["rn"]] + o["off"]) & MASK64, 8)
            state.pc += 4
        elif m == "STR":
            state.write_mem((state.regs[o["rn"]] + o["off"]) & MASK64, 8, state.regs[o["rt"]])
            state.pc += 4
        elif m in ("B", "BL"):
            if m == "BL":
                state.regs[30] = u64(state.pc + 4)
            state.pc = u64(state.pc + 4 + o["off"])
        elif m in ("BR", "BLR"):
            if m == "BLR":
                state.regs[30] = u64(state.pc + 4)
            state.pc = u64(state.regs[o["rn"]])
        elif m == "RET":
            state.pc = u64(state.regs[o["rn"]])
        elif m == "SVC":
            state.trap = f"SVC #{o['imm']}"
            state.halted = True
            state.pc += 4
        elif m == "NOP":
            state.pc += 4
        else:
            raise IllegalInstruction(f"no execution semantics for {m}")

    def effects(self, decoded: Decoded) -> dict[str, Any]:
        m, o = decoded.mnemonic, decoded.operands
        reads: list[str] = []
        writes: list[str] = []
        memory = "none"
        if "rn" in o:
            reads.append(f"X{o['rn']}")
        if "rm" in o:
            reads.append(f"X{o['rm']}")
        if m in ("ADD", "SUB", "AND", "ORR", "EOR") and "rd" in o:
            writes.append(f"X{o['rd']}")
        if m == "LDR":
            writes.append(f"X{o['rt']}")
            memory = "read"
        elif m == "STR":
            reads.append(f"X{o['rt']}")
            memory = "write"
        elif m in ("BL", "BLR"):
            writes.append("X30")
        return {
            "registers_read": sorted(set(reads)), "registers_written": sorted(set(writes)),
            "registers_clobbered": [], "flags_read": [], "flags_written": [],
            "memory_effects": memory,
            "privilege": "user (SVC traps to supervisor)" if m == "SVC" else "user",
        }

# ---------------------------------------------------------------------------
# RV64I RISC: 32-bit fixed-width instructions, 64-bit register semantics
# ---------------------------------------------------------------------------

R_TYPE = {"ADD": (0, 0), "SLL": (0, 1), "SLT": (0, 2), "SLTU": (0, 3), "XOR": (0, 4),
          "SRL": (0, 5), "OR": (0, 6), "AND": (0, 7), "SUB": (0x20, 0), "SRA": (0x20, 5)}
I_TYPE = {"ADDI": 0, "SLTI": 2, "SLTIU": 3, "XORI": 4, "ORI": 6, "ANDI": 7}
LOADS = {"LBU": 4, "LH": 1, "LW": 2}
STORES = {"SB": 0, "SH": 1, "SW": 2}
BRANCHES = {"BEQ": 0}
SYSTEM = {"ECALL": 0x00000073, "EBREAK": 0x00100073, "MRET": 0x30200073}


def _rv_reg(token: str) -> int:
    m = re.fullmatch(r"[xX](\d+)", str(token).strip())
    if not m:
        raise ValueError(f"unsupported RISC-V register: {token}")
    index = int(m.group(1))
    if index > 31:
        raise ValueError("register must be x0..x31")
    return index


class Riscv64Backend:
    arch = "riscv64"
    family = "RISC riscv64"
    endian = "instruction-little"

    def formats(self) -> dict[tuple[str, str], dict[str, Any]]:
        base = {"semantic_class": "integer"}
        out: dict[tuple[str, str], dict[str, Any]] = {}
        for m in R_TYPE:
            out[(m, "rrr")] = dict(base, format_class="RV64 R-type", opcode="0x33", bit_fields=[
                {"name": "funct7", "bits": "31:25", "role": "operation"},
                {"name": "rs2", "bits": "24:20", "role": "source 2"},
                {"name": "rs1", "bits": "19:15", "role": "source 1"},
                {"name": "funct3", "bits": "14:12", "role": "operation"},
                {"name": "rd", "bits": "11:7", "role": "destination"},
                {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        for m in I_TYPE:
            out[(m, "ri")] = dict(base, format_class="RV64 I-type", opcode="0x13", bit_fields=[
                {"name": "imm[11:0]", "bits": "31:20", "role": "sign-extended immediate"},
                {"name": "rs1", "bits": "19:15", "role": "source"},
                {"name": "funct3", "bits": "14:12", "role": "operation"},
                {"name": "rd", "bits": "11:7", "role": "destination"},
                {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        for m in LOADS:
            out[(m, "load")] = dict(base, format_class="RV64 I-type load", opcode="0x03", bit_fields=[
                {"name": "imm[11:0]", "bits": "31:20", "role": "offset"}, {"name": "rs1", "bits": "19:15", "role": "base"},
                {"name": "funct3", "bits": "14:12", "role": "width/sign"}, {"name": "rd", "bits": "11:7", "role": "destination"},
                {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        for m in STORES:
            out[(m, "store")] = dict(base, format_class="RV64 S-type", opcode="0x23", bit_fields=[
                {"name": "imm[11:5]", "bits": "31:25", "role": "offset high"}, {"name": "rs2", "bits": "24:20", "role": "source"},
                {"name": "rs1", "bits": "19:15", "role": "base"}, {"name": "funct3", "bits": "14:12", "role": "width"},
                {"name": "imm[4:0]", "bits": "11:7", "role": "offset low"}, {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        out[("BEQ", "branch")] = dict(base, format_class="RV64 B-type", opcode="0x63", bit_fields=[
            {"name": "imm[12|10:5]", "bits": "31:25", "role": "offset high"}, {"name": "rs2", "bits": "24:20", "role": "source 2"},
            {"name": "rs1", "bits": "19:15", "role": "source 1"}, {"name": "funct3", "bits": "14:12", "role": "condition"},
            {"name": "imm[4:1|11]", "bits": "11:7", "role": "offset low"}, {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        for m in ("LUI", "AUIPC"):
            out[(m, "u")] = dict(base, format_class="RV64 U-type", opcode="0x37" if m == "LUI" else "0x17", bit_fields=[
                {"name": "imm[31:12]", "bits": "31:12", "role": "upper immediate"},
                {"name": "rd", "bits": "11:7", "role": "destination"}, {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        out[("JAL", "jal")] = dict(base, format_class="RV64 J-type", opcode="0x6F", bit_fields=[
            {"name": "imm[20|10:1|11|19:12]", "bits": "31:12", "role": "jump offset"},
            {"name": "rd", "bits": "11:7", "role": "link register"}, {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        out[("JALR", "jalr")] = dict(base, format_class="RV64 I-type", opcode="0x67", bit_fields=[
            {"name": "imm[11:0]", "bits": "31:20", "role": "offset"}, {"name": "rs1", "bits": "19:15", "role": "base"},
            {"name": "funct3", "bits": "14:12", "role": "must be 0"}, {"name": "rd", "bits": "11:7", "role": "link register"},
            {"name": "opcode", "bits": "6:0", "role": "opcode"}])
        out[("FENCE", "fence")] = dict(base, format_class="RV64 I-type fence", opcode="0x0F", bit_fields=[
            {"name": "pred", "bits": "27:24", "role": "predecessor set"}, {"name": "succ", "bits": "23:20", "role": "successor set"},
            {"name": "opcode", "bits": "6:0", "role": "opcode"}], semantic_class="memory")
        for m in SYSTEM:
            out[(m, "system")] = dict(base, format_class="RV64 SYSTEM", opcode=f"0x{SYSTEM[m]:08x}",
                                      bit_fields=[{"name": "fixed", "bits": "31:0", "role": "system opcode"}],
                                      semantic_class="system")
        return out

    @staticmethod
    def _imm(value: int, bits: int, what: str) -> int:
        if value < -(1 << (bits - 1)) or value >= (1 << (bits - 1)):
            raise ValueError(f"{what} out of signed {bits}-bit range")
        return value & ((1 << bits) - 1)

    def assemble(self, line: str) -> Decoded:
        text = line.split("#", 1)[0].strip()
        parts = text.replace(",", " ").replace("(", " ").replace(")", "").split()
        if not parts:
            raise ValueError("empty instruction")
        m = parts[0].upper()
        a = parts[1:]
        if m in SYSTEM and not a:
            word = SYSTEM[m]
            return Decoded(self.arch, m, "system", {}, m, struct.pack("<I", word))
        if m == "FENCE" and not a:
            word = (0xF << 24) | (0xF << 20) | 0x0F
            return Decoded(self.arch, m, "fence", {"pred": 15, "succ": 15}, "FENCE", struct.pack("<I", word))
        if m in R_TYPE and len(a) == 3:
            rd, rs1, rs2 = map(_rv_reg, a)
            f7, f3 = R_TYPE[m]
            word = (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x33
            canonical = f"{m} x{rd},x{rs1},x{rs2}"
            return Decoded(self.arch, m, "rrr", {"rd": rd, "rs1": rs1, "rs2": rs2}, canonical, struct.pack("<I", word))
        if m in I_TYPE and len(a) == 3:
            rd, rs1 = _rv_reg(a[0]), _rv_reg(a[1])
            imm = parse_int(a[2])
            word = (self._imm(imm, 12, "I-immediate") << 20) | (rs1 << 15) | (I_TYPE[m] << 12) | (rd << 7) | 0x13
            canonical = f"{m} x{rd},x{rs1},{imm}"
            return Decoded(self.arch, m, "ri", {"rd": rd, "rs1": rs1, "imm": imm}, canonical, struct.pack("<I", word))
        if m in LOADS and len(a) == 3:
            rd, off, rs1 = _rv_reg(a[0]), parse_int(a[1]), _rv_reg(a[2])
            word = (self._imm(off, 12, "load offset") << 20) | (rs1 << 15) | (LOADS[m] << 12) | (rd << 7) | 0x03
            canonical = f"{m} x{rd},{off}(x{rs1})"
            return Decoded(self.arch, m, "load", {"rd": rd, "rs1": rs1, "off": off}, canonical, struct.pack("<I", word))
        if m in STORES and len(a) == 3:
            rs2, off, rs1 = _rv_reg(a[0]), parse_int(a[1]), _rv_reg(a[2])
            u = self._imm(off, 12, "store offset")
            word = ((u >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (STORES[m] << 12) | ((u & 31) << 7) | 0x23
            canonical = f"{m} x{rs2},{off}(x{rs1})"
            return Decoded(self.arch, m, "store", {"rs2": rs2, "rs1": rs1, "off": off}, canonical, struct.pack("<I", word))
        if m in BRANCHES and len(a) == 3:
            rs1, rs2, off = _rv_reg(a[0]), _rv_reg(a[1]), parse_int(a[2])
            if off % 2:
                raise ValueError("branch offset must be even")
            u = self._imm(off, 13, "branch offset")
            word = (((u >> 12) & 1) << 31) | (((u >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (BRANCHES[m] << 12) | (((u >> 1) & 0xF) << 8) | (((u >> 11) & 1) << 7) | 0x63
            canonical = f"{m} x{rs1},x{rs2},{off}"
            return Decoded(self.arch, m, "branch", {"rs1": rs1, "rs2": rs2, "off": off}, canonical, struct.pack("<I", word))
        if m in ("LUI", "AUIPC") and len(a) == 2:
            rd = _rv_reg(a[0])
            value = parse_int(a[1])
            if value < 0:
                value &= (1 << 20) - 1
            if value > 0xFFFFF:
                raise ValueError("U-immediate out of 20-bit range")
            word = (value << 12) | (rd << 7) | (0x37 if m == "LUI" else 0x17)
            canonical = f"{m} x{rd},0x{value:x}"
            return Decoded(self.arch, m, "u", {"rd": rd, "imm": value << 12}, canonical, struct.pack("<I", word))
        if m == "JAL" and len(a) == 2:
            rd, off = _rv_reg(a[0]), parse_int(a[1])
            if off % 2:
                raise ValueError("JAL offset must be even")
            u = self._imm(off, 21, "JAL offset")
            word = (((u >> 20) & 1) << 31) | (((u >> 1) & 0x3FF) << 21) | (((u >> 11) & 1) << 20) | (((u >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F
            canonical = f"JAL x{rd},{off}"
            return Decoded(self.arch, m, "jal", {"rd": rd, "off": off}, canonical, struct.pack("<I", word))
        if m == "JALR" and len(a) == 3:
            rd, off, rs1 = _rv_reg(a[0]), parse_int(a[1]), _rv_reg(a[2])
            word = (self._imm(off, 12, "JALR offset") << 20) | (rs1 << 15) | (rd << 7) | 0x67
            canonical = f"JALR x{rd},{off}(x{rs1})"
            return Decoded(self.arch, m, "jalr", {"rd": rd, "rs1": rs1, "off": off}, canonical, struct.pack("<I", word))
        raise ValueError(f"unsupported RV64I slice instruction: {text}")

    def disassemble(self, data: bytes) -> Decoded:
        if len(data) != 4:
            raise IllegalInstruction("RV64I instructions are exactly 4 bytes")
        w = struct.unpack("<I", data)[0]
        if w in SYSTEM.values():
            m = next(name for name, value in SYSTEM.items() if value == w)
            return Decoded(self.arch, m, "system", {}, m, data, {"word": w})
        if (w & 0x7F) == 0x0F:
            return Decoded(self.arch, "FENCE", "fence", {"pred": (w >> 24) & 15, "succ": (w >> 20) & 15}, "FENCE", data, {"word": w})
        opcode, rd, f3, rs1, rs2, f7 = w & 0x7F, (w >> 7) & 31, (w >> 12) & 7, (w >> 15) & 31, (w >> 20) & 31, w >> 25
        if opcode == 0x33:
            table = {(v[0], v[1]): k for k, v in R_TYPE.items()}
            if (f7, f3) not in table:
                raise IllegalInstruction(f"reserved RV64 R-type encoding 0x{w:08x}")
            m = table[(f7, f3)]
            return Decoded(self.arch, m, "rrr", {"rd": rd, "rs1": rs1, "rs2": rs2}, f"{m} x{rd},x{rs1},x{rs2}", data, {"word": w})
        if opcode == 0x13:
            table = {v: k for k, v in I_TYPE.items()}
            if f3 not in table:
                raise IllegalInstruction(f"reserved RV64 OP-IMM encoding 0x{w:08x}")
            m = table[f3]
            imm = sx(w >> 20, 12)
            return Decoded(self.arch, m, "ri", {"rd": rd, "rs1": rs1, "imm": imm}, f"{m} x{rd},x{rs1},{imm}", data, {"word": w})
        if opcode == 0x03:
            table = {v: k for k, v in LOADS.items()}
            if f3 not in table:
                raise IllegalInstruction(f"reserved RV64 load encoding 0x{w:08x}")
            m = table[f3]
            off = sx(w >> 20, 12)
            return Decoded(self.arch, m, "load", {"rd": rd, "rs1": rs1, "off": off}, f"{m} x{rd},{off}(x{rs1})", data, {"word": w})
        if opcode == 0x23:
            table = {v: k for k, v in STORES.items()}
            if f3 not in table:
                raise IllegalInstruction(f"reserved RV64 store encoding 0x{w:08x}")
            m = table[f3]
            off = sx(((w >> 25) << 5) | ((w >> 7) & 31), 12)
            return Decoded(self.arch, m, "store", {"rs2": rs2, "rs1": rs1, "off": off}, f"{m} x{rs2},{off}(x{rs1})", data, {"word": w})
        if opcode == 0x63 and f3 in BRANCHES.values():
            m = next(k for k, v in BRANCHES.items() if v == f3)
            bits = (((w >> 31) & 1) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 0x3F) << 5) | (((w >> 8) & 0xF) << 1)
            off = sx(bits, 13)
            return Decoded(self.arch, m, "branch", {"rs1": rs1, "rs2": rs2, "off": off}, f"{m} x{rs1},x{rs2},{off}", data, {"word": w})
        if opcode in (0x37, 0x17):
            m = "LUI" if opcode == 0x37 else "AUIPC"
            imm = (w >> 12) << 12
            return Decoded(self.arch, m, "u", {"rd": rd, "imm": imm}, f"{m} x{rd},0x{imm >> 12:x}", data, {"word": w})
        if opcode == 0x6F:
            bits = (((w >> 31) & 1) << 20) | (((w >> 12) & 0xFF) << 12) | (((w >> 20) & 1) << 11) | (((w >> 21) & 0x3FF) << 1)
            off = sx(bits, 21)
            return Decoded(self.arch, "JAL", "jal", {"rd": rd, "off": off}, f"JAL x{rd},{off}", data, {"word": w})
        if opcode == 0x67 and f3 == 0:
            off = sx(w >> 20, 12)
            return Decoded(self.arch, "JALR", "jalr", {"rd": rd, "rs1": rs1, "off": off}, f"JALR x{rd},{off}(x{rs1})", data, {"word": w})
        raise IllegalInstruction(f"unimplemented or illegal RV64I encoding 0x{w:08x}")

    def step(self, decoded: Decoded, state: State) -> None:
        m, o = decoded.mnemonic, decoded.operands
        regs = state.regs
        if m in R_TYPE:
            a, b = regs[o["rs1"]], regs[o["rs2"]]
            sh = b & 63
            value = {"ADD": a + b, "SUB": a - b, "SLL": a << sh, "SLT": int(sx(a, 64) < sx(b, 64)),
                     "SLTU": int((a & MASK64) < (b & MASK64)), "XOR": a ^ b, "SRL": (a & MASK64) >> sh,
                     "SRA": sx(a, 64) >> sh, "OR": a | b, "AND": a & b}[m]
            if o["rd"]:
                regs[o["rd"]] = u64(value)
            state.pc += 4
        elif m in I_TYPE:
            a = regs[o["rs1"]]
            value = {"ADDI": a + o["imm"], "SLTI": int(sx(a, 64) < o["imm"]), "SLTIU": int(a < (o["imm"] & MASK64)),
                     "XORI": a ^ o["imm"], "ORI": a | o["imm"], "ANDI": a & o["imm"]}[m]
            if o["rd"]:
                regs[o["rd"]] = u64(value)
            state.pc += 4
        elif m in LOADS:
            size = {"LBU": 1, "LH": 2, "LW": 4}[m]
            address = u64(regs[o["rs1"]] + o["off"])
            value = state.read_mem(address, size)
            if m == "LH":
                value = sx(value, 16) & MASK64
            elif m == "LW":
                value = sx(value, 32) & MASK64
            if o["rd"]:
                regs[o["rd"]] = u64(value)
            state.pc += 4
        elif m in STORES:
            size = {"SB": 1, "SH": 2, "SW": 4}[m]
            address = u64(regs[o["rs1"]] + o["off"])
            state.write_mem(address, size, regs[o["rs2"]])
            state.pc += 4
        elif m == "BEQ":
            state.pc = u64(state.pc + 4 + o["off"]) if regs[o["rs1"]] == regs[o["rs2"]] else u64(state.pc + 4)
        elif m in ("LUI", "AUIPC"):
            value = o["imm"] if m == "LUI" else u64(state.pc + o["imm"])
            if o["rd"]:
                regs[o["rd"]] = u64(value)
            state.pc += 4
        elif m == "JAL":
            if o["rd"]:
                regs[o["rd"]] = u64(state.pc + 4)
            state.pc = u64(state.pc + 4 + o["off"])
        elif m == "JALR":
            target = u64(regs[o["rs1"]] + o["off"]) & ~1
            if o["rd"]:
                regs[o["rd"]] = u64(state.pc + 4)
            state.pc = u64(target)
        elif m == "ECALL":
            state.trap = "ECALL"; state.halted = True; state.pc += 4
        elif m == "EBREAK":
            state.trap = "EBREAK"; state.halted = True; state.pc += 4
        elif m == "MRET":
            state.trap = "MRET"; state.halted = True; state.pc += 4
        elif m == "FENCE":
            state.pc += 4
        else:
            raise IllegalInstruction(f"no execution semantics for {m}")
        regs[0] = 0

    def effects(self, decoded: Decoded) -> dict[str, Any]:
        m, o = decoded.mnemonic, decoded.operands
        reads = [f"x{v}" for k, v in o.items() if k in ("rs1", "rs2") and v]
        writes = [f"x{o['rd']}"] if o.get("rd") else []
        memory = "none"
        if m in LOADS:
            memory = "read"
        elif m in STORES:
            memory = "write"
        elif m in ("FENCE",):
            memory = "ordering barrier"
        priv = "supervisor (MRET/SVC-class)" if m in ("MRET",) else "user"
        return {"registers_read": reads, "registers_written": writes, "registers_clobbered": [],
                "flags_read": [], "flags_written": [], "memory_effects": memory, "privilege": priv}


BACKENDS: dict[str, Any] = {
    "x86-64": X86Backend(),
    "aarch64": AArch64Backend(),
    "riscv64": Riscv64Backend(),
}
CATALOG_VECTORS: dict[tuple[str, str, str], str] = {
    # x86-64 CISC: canonical instruction text whose fixed bits match the sourced mask.
    ("x86-64", "ADD", "rm64_r64"): "ADD [RAX],RAX",
    ("x86-64", "AND", "rm64_r64"): "AND [RAX],RAX",
    ("x86-64", "CALL", "rel32"): "CALL 0",
    ("x86-64", "JMP", "rel32"): "JMP 0",
    ("x86-64", "MOV", "r64_rm64"): "MOV RAX,[RAX]",
    ("x86-64", "MOV", "rm64_r64"): "MOV [RAX],RAX",
    ("x86-64", "NOP", "fixed"): "NOP",
    ("x86-64", "OR", "rm64_r64"): "OR [RAX],RAX",
    ("x86-64", "POP", "r64"): "POP RAX",
    ("x86-64", "PUSH", "r64"): "PUSH RAX",
    ("x86-64", "RET", "fixed"): "RET",
    ("x86-64", "SUB", "rm64_r64"): "SUB [RAX],RAX",
    ("x86-64", "XOR", "rm64_r64"): "XOR [RAX],RAX",
    # AArch64 RISC.
    ("aarch64", "ADD", "imm"): "ADD X0,X1,#1",
    ("aarch64", "ADD", "rrr"): "ADD X0,X1,X2",
    ("aarch64", "AND", "rrr"): "AND X0,X1,X2",
    ("aarch64", "B", "imm"): "B 0",
    ("aarch64", "BL", "imm"): "BL 0",
    ("aarch64", "BLR", "reg"): "BLR X0",
    ("aarch64", "BR", "reg"): "BR X0",
    ("aarch64", "EOR", "rrr"): "EOR X0,X1,X2",
    ("aarch64", "LDR", "unsigned"): "LDR X0,[X1,#0]",
    ("aarch64", "NOP", "none"): "NOP",
    ("aarch64", "ORR", "rrr"): "ORR X0,X1,X2",
    ("aarch64", "RET", "reg"): "RET X30",
    ("aarch64", "STR", "unsigned"): "STR X0,[X1,#0]",
    ("aarch64", "SUB", "imm"): "SUB X0,X1,#1",
    ("aarch64", "SUB", "rrr"): "SUB X0,X1,X2",
    ("aarch64", "SVC", "imm"): "SVC #0",
    # RV64I RISC.
    ("riscv64", "ADD", "rrr"): "ADD x1,x2,x3",
    ("riscv64", "ADDI", "ri"): "ADDI x1,x2,5",
    ("riscv64", "AND", "rrr"): "AND x1,x2,x3",
    ("riscv64", "ANDI", "ri"): "ANDI x1,x2,1",
    ("riscv64", "AUIPC", "u"): "AUIPC x1,0x1",
    ("riscv64", "BEQ", "branch"): "BEQ x1,x2,8",
    ("riscv64", "EBREAK", "system"): "EBREAK",
    ("riscv64", "ECALL", "system"): "ECALL",
    ("riscv64", "FENCE", "fence"): "FENCE",
    ("riscv64", "JAL", "jal"): "JAL x1,8",
    ("riscv64", "JALR", "jalr"): "JALR x1,0(x2)",
    ("riscv64", "LBU", "load"): "LBU x1,8(x2)",
    ("riscv64", "LH", "load"): "LH x1,8(x2)",
    ("riscv64", "LUI", "u"): "LUI x1,0x1",
    ("riscv64", "LW", "load"): "LW x1,8(x2)",
    ("riscv64", "MRET", "system"): "MRET",
    ("riscv64", "OR", "rrr"): "OR x1,x2,x3",
    ("riscv64", "ORI", "ri"): "ORI x1,x2,1",
    ("riscv64", "SB", "store"): "SB x3,8(x2)",
    ("riscv64", "SH", "store"): "SH x3,8(x2)",
    ("riscv64", "SLL", "rrr"): "SLL x1,x2,x3",
    ("riscv64", "SLT", "rrr"): "SLT x1,x2,x3",
    ("riscv64", "SLTI", "ri"): "SLTI x1,x2,1",
    ("riscv64", "SLTU", "rrr"): "SLTU x1,x2,x3",
    ("riscv64", "SRA", "rrr"): "SRA x1,x2,x3",
    ("riscv64", "SRL", "rrr"): "SRL x1,x2,x3",
    ("riscv64", "SUB", "rrr"): "SUB x1,x2,x3",
    ("riscv64", "SW", "store"): "SW x3,8(x2)",
    ("riscv64", "XOR", "rrr"): "XOR x1,x2,x3",
    ("riscv64", "XORI", "ri"): "XORI x1,x2,1",
}
SUPPORTED_FORM_KEYS = {(arch, key) for arch, backend in BACKENDS.items() for key in backend.formats()}


def assemble(arch: str, line: str) -> Decoded:
    backend = BACKENDS.get(arch)
    if backend is None:
        raise ValueError(f"no real backend for architecture {arch}")
    return backend.assemble(line)


def disassemble(arch: str, data: bytes) -> Decoded:
    backend = BACKENDS.get(arch)
    if backend is None:
        raise ValueError(f"no real backend for architecture {arch}")
    return backend.disassemble(data)


def effects(arch: str, decoded: Decoded) -> dict[str, Any]:
    return BACKENDS[arch].effects(decoded)


def step(arch: str, decoded: Decoded, state: State) -> None:
    BACKENDS[arch].step(decoded, state)


# ---------------------------------------------------------------------------
# Versioned Chimera native object format (CHMOBJ1)
# ---------------------------------------------------------------------------

OBJ_MAGIC = b"CHMOBJ1\0"
OBJ_VERSION = 1
OBJ_ABI_VERSION = 1
OBJ_HEADER_STRUCT = struct.Struct("<8sHHIHHHHIIIIII")
# magic, format_version, header_size, abi_version, arch_id_crc, flags,
# section_count, symbol_count, reloc_count, section_off, symbol_off, reloc_off,
# data_off, total_size  (64 bytes with 8-byte alignment via padding below)
OBJ_HEADER_SIZE = 64
SECTION_STRUCT = struct.Struct("<IBBBBQQQ")   # name_off, type, perms, align, reserved, address, offset, size = 40
SYMBOL_STRUCT = struct.Struct("<IBBHQQ")      # name_off, type, bind, shndx, value, size = 32
RELOC_STRUCT = struct.Struct("<HHBBqQ")       # section, symbol, type, width, addend, offset = 32
SECTION_TYPES = {"NULL": 0, "PROGBITS": 1, "NOBITS": 2, "STRTAB": 3, "SYMTAB": 4, "RELATAB": 5, "NOTE": 6}
PERM_READ, PERM_WRITE, PERM_EXEC = 1, 2, 4
RELOC_ABS64, RELOC_ABS32, RELOC_REL32 = 1, 2, 3
RELOC_WIDTHS = {RELOC_ABS64: 64, RELOC_ABS32: 32, RELOC_REL32: 32}


def arch_identity(arch: str) -> tuple[int, str]:
    import zlib
    name = arch.strip().lower()
    return zlib.crc32(name.encode("utf-8")) & 0xFFFF, name


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


@dataclass
class Section:
    name: str
    type: int
    perms: int
    align: int
    address: int
    data: bytes
    size: int = 0

    @property
    def is_nobits(self) -> bool:
        return self.type == SECTION_TYPES["NOBITS"]


@dataclass
class Symbol:
    name: str
    type: int = 0
    bind: int = 1
    shndx: int = 0
    value: int = 0
    size: int = 0


@dataclass
class Relocation:
    section: int
    symbol: int
    type: int
    addend: int
    offset: int


@dataclass
class NativeObject:
    arch: str
    abi_version: int
    flags: int
    sections: list[Section]
    symbols: list[Symbol]
    relocations: list[Relocation]
    digest: bytes


def build_object(arch: str, sections: list[Section], symbols: list[Symbol],
                 relocations: list[Relocation], abi_version: int = OBJ_ABI_VERSION,
                 flags: int = 0) -> bytes:
    """Serialize a CHMOBJ1 image. Structurally invalid inputs are rejected."""
    crc, _ = arch_identity(arch)
    if not sections or sections[0].name != "" or sections[0].type != SECTION_TYPES["NULL"]:
        raise ObjectFormatError("section 0 must be the null section")
    if abi_version != OBJ_ABI_VERSION:
        raise ObjectFormatError("unsupported ABI version")
    if flags & ~(PERM_READ | PERM_WRITE | PERM_EXEC):
        raise ObjectFormatError("unknown object flags")
    sections = [Section(s.name, s.type, s.perms, s.align, s.address, bytes(s.data), s.size)
                for s in sections]
    strtab = next((s for s in sections if s.type == SECTION_TYPES["STRTAB"]), None)
    if strtab is None:
        raise ObjectFormatError("object requires a .strtab section")
    names = bytearray(b"\0")
    name_offsets: dict[str, int] = {"": 0}

    def name_off(name: str) -> int:
        if name not in name_offsets:
            name_offsets[name] = len(names)
            names.extend(name.encode("utf-8") + b"\0")
        return name_offsets[name]

    for section in sections:
        name_off(section.name)
    for symbol in symbols:
        name_off(symbol.name)
    strtab.data = bytes(names)
    strtab.size = len(names)
    symbols_bytes = b"".join(SYMBOL_STRUCT.pack(name_off(s.name), s.type, s.bind, s.shndx, s.value, s.size)
                             for s in symbols)
    reloc_bytes = b"".join(RELOC_STRUCT.pack(r.section, r.symbol, r.type,
                                             RELOC_WIDTHS.get(r.type, 0), r.addend, r.offset)
                           for r in relocations)
    for section in sections:
        if section.type == SECTION_TYPES["SYMTAB"]:
            section.data, section.size = symbols_bytes, len(symbols_bytes)
        elif section.type == SECTION_TYPES["RELATAB"]:
            section.data, section.size = reloc_bytes, len(reloc_bytes)
        if section.align < 1 or section.align & (section.align - 1):
            raise ObjectFormatError("section alignment must be a power of two")
        if section.is_nobits:
            if section.data:
                raise ObjectFormatError("NOBITS section must not carry bytes")
        elif section.size and section.size != len(section.data):
            raise ObjectFormatError(f"section {section.name!r} size does not match its data")
        elif not section.size:
            section.size = len(section.data)
    for i, symbol in enumerate(symbols):
        if symbol.shndx >= len(sections):
            raise ObjectFormatError(f"symbol {i} section index is out of bounds")
    for i, rel in enumerate(relocations):
        if rel.section == 0 or rel.section >= len(sections) or rel.symbol >= len(symbols):
            raise ObjectFormatError(f"relocation {i} index is out of bounds")
        if rel.type not in RELOC_WIDTHS:
            raise ObjectFormatError(f"relocation {i} has unsupported type")
        width = RELOC_WIDTHS[rel.type] // 8
        if rel.offset + width > sections[rel.section].size:
            raise ObjectFormatError(f"relocation {i} is outside its section")

    section_off = OBJ_HEADER_SIZE
    sections_bytes = b"".join(SECTION_STRUCT.pack(name_off(s.name), s.type, s.perms, s.align, 0,
                                                   s.address, 0, s.size) for s in sections)
    symbol_off = _align(section_off + len(sections_bytes), 8)
    reloc_off = _align(symbol_off + len(symbols_bytes), 8)
    data_off = _align(reloc_off + len(reloc_bytes), 16)
    offsets: list[int] = []
    cursor = data_off
    for section in sections:
        cursor = _align(cursor, section.align)
        offsets.append(cursor)
        cursor += section.size
    total = _align(cursor, 16)
    sections_bytes = b"".join(SECTION_STRUCT.pack(name_off(s.name), s.type, s.perms, s.align, 0,
                                                   s.address, offsets[i], s.size)
                              for i, s in enumerate(sections))
    header = OBJ_HEADER_STRUCT.pack(OBJ_MAGIC, OBJ_VERSION, OBJ_HEADER_SIZE, abi_version, crc, flags,
                                    len(sections), len(symbols), len(relocations), section_off, symbol_off,
                                    reloc_off, data_off, total)
    header += b"\0" * (OBJ_HEADER_SIZE - len(header))
    out = bytearray(header)
    out.extend(sections_bytes)
    out.extend(b"\0" * (symbol_off - len(out)))
    out.extend(symbols_bytes)
    out.extend(b"\0" * (reloc_off - len(out)))
    out.extend(reloc_bytes)
    out.extend(b"\0" * (data_off - len(out)))
    for i, section in enumerate(sections):
        out.extend(b"\0" * (offsets[i] - len(out)))
        if not section.is_nobits:
            out.extend(section.data)
    out.extend(b"\0" * (total - len(out)))
    if len(out) != total:
        raise ObjectFormatError("internal object layout error")
    return bytes(out) + hashlib.sha256(bytes(out)).digest()


def validate_object(data: bytes, expected_arch: str | None = None, arch_names: list[str] | None = None) -> NativeObject:
    """Strictly validate a CHMOBJ1 image. Any structural error raises."""
    if len(data) < OBJ_HEADER_SIZE + 32:
        raise ObjectFormatError("object is too short")
    body, digest = data[:-32], data[-32:]
    if hashlib.sha256(body).digest() != digest:
        raise ObjectFormatError("object digest mismatch")
    (magic, version, header_size, abi, crc, flags, nsec, nsym, nreloc, sec_off, sym_off,
     rel_off, data_off, total) = OBJ_HEADER_STRUCT.unpack_from(body, 0)
    if magic != OBJ_MAGIC:
        raise ObjectFormatError("bad magic")
    if version != OBJ_VERSION:
        raise ObjectFormatError("unsupported object version")
    if header_size != OBJ_HEADER_SIZE or abi != OBJ_ABI_VERSION:
        raise ObjectFormatError("unsupported header or ABI version")
    if len(body) != total or total % 16:
        raise ObjectFormatError("declared size does not match file")
    if flags & ~(PERM_READ | PERM_WRITE | PERM_EXEC):
        raise ObjectFormatError("unknown object flags")
    names = arch_names or list(BACKENDS)
    arch = next((name for name in names if arch_identity(name)[0] == crc), None)
    if arch is None:
        raise ObjectFormatError("unknown architecture id")
    if expected_arch is not None and expected_arch != arch:
        raise ObjectFormatError("architecture id does not match expected architecture")
    if nsec == 0 or nsec > 4096 or nsym > 1_000_000 or nreloc > 1_000_000:
        raise ObjectFormatError("implausible table counts")
    needed = max(sec_off + nsec * SECTION_STRUCT.size, sym_off + nsym * SYMBOL_STRUCT.size,
                 rel_off + nreloc * RELOC_STRUCT.size, data_off)
    if needed > total or sec_off < OBJ_HEADER_SIZE or sym_off < sec_off or rel_off < sym_off or data_off < rel_off:
        raise ObjectFormatError("table offsets are out of bounds or overlap headers")
    raw_sections = [SECTION_STRUCT.unpack_from(body, sec_off + i * SECTION_STRUCT.size) for i in range(nsec)]
    if raw_sections[0][1] != SECTION_TYPES["NULL"] or raw_sections[0][0] != 0:
        raise ObjectFormatError("section 0 must be NULL with an empty name")
    strtab_indices = [i for i, raw in enumerate(raw_sections) if raw[1] == SECTION_TYPES["STRTAB"]]
    if len(strtab_indices) != 1:
        raise ObjectFormatError("object must contain exactly one string table")
    strtab_index = strtab_indices[0]
    intervals: list[tuple[int, int]] = []
    sections: list[Section] = []
    for i, raw in enumerate(raw_sections):
        name_off, stype, perms, align, reserved, address, offset, size = raw
        if reserved or stype > max(SECTION_TYPES.values()) or perms & ~(PERM_READ | PERM_WRITE | PERM_EXEC):
            raise ObjectFormatError(f"invalid section record {i}")
        if align == 0 or align & (align - 1):
            raise ObjectFormatError(f"section {i} alignment is not a power of two")
        if stype == SECTION_TYPES["NOBITS"]:
            payload = b""
        else:
            if offset < data_off or offset + size > total:
                raise ObjectFormatError(f"section {i} data is out of bounds")
            payload = body[offset:offset + size]
            if size:
                intervals.append((offset, offset + size))
        sections.append(Section("", stype, perms, align, address, payload, size))
    intervals.sort()
    for (a1, b1), (a2, b2) in zip(intervals, intervals[1:]):
        if a2 < b1:
            raise ObjectFormatError("section payloads overlap")
    strings = sections[strtab_index].data
    if not strings or strings[0] != 0:
        raise ObjectFormatError("string table must start with NUL")

    def read_name(offset: int) -> str:
        if offset >= len(strings):
            raise ObjectFormatError("string offset out of bounds")
        end = strings.find(b"\0", offset)
        if end < 0:
            raise ObjectFormatError("unterminated string")
        return strings[offset:end].decode("utf-8")

    for i, raw in enumerate(raw_sections):
        sections[i].name = read_name(raw[0])
    symbols: list[Symbol] = []
    for i in range(nsym):
        name_off, stype, bind, shndx, value, size = SYMBOL_STRUCT.unpack_from(body, sym_off + i * SYMBOL_STRUCT.size)
        if shndx >= nsec or bind > 2 or stype > 6:
            raise ObjectFormatError(f"invalid symbol record {i}")
        symbols.append(Symbol(read_name(name_off), stype, bind, shndx, value, size))
    relocations: list[Relocation] = []
    for i in range(nreloc):
        sec, sym, rtype, width, addend, offset = RELOC_STRUCT.unpack_from(body, rel_off + i * RELOC_STRUCT.size)
        if sec == 0 or sec >= nsec or sym >= nsym:
            raise ObjectFormatError(f"invalid relocation record {i}")
        if rtype not in RELOC_WIDTHS or width != RELOC_WIDTHS[rtype]:
            raise ObjectFormatError(f"unsupported relocation type/width {rtype}/{width}")
        if offset + width // 8 > sections[sec].size:
            raise ObjectFormatError(f"relocation {i} is outside its section")
        relocations.append(Relocation(sec, sym, rtype, addend, offset))
    return NativeObject(arch, abi, flags, sections, symbols, relocations, digest)


def demo_object(arch: str = "riscv64", line: str = "ADDI x1,x2,5") -> bytes:
    """Create a small, fully valid object containing one encoded instruction."""
    decoded = assemble(arch, line)
    text = Section(".text", SECTION_TYPES["PROGBITS"], PERM_READ | PERM_EXEC, 4, 0x1000, decoded.data, len(decoded.data))
    strtab = Section(".strtab", SECTION_TYPES["STRTAB"], PERM_READ, 1, 0, b"", 0)
    symtab = Section(".symtab", SECTION_TYPES["SYMTAB"], PERM_READ, 8, 0, b"", 0)
    reltab = Section(".relatab", SECTION_TYPES["RELATAB"], PERM_READ, 8, 0, b"", 0)
    return build_object(arch,
                        [Section("", SECTION_TYPES["NULL"], 0, 1, 0, b"", 0), text, strtab, symtab, reltab],
                        [Symbol("", 0, 0, 0, 0, 0), Symbol("entry", 2, 1, 1, 0x1000, len(decoded.data))],
                        [Relocation(1, 1, RELOC_ABS32, 0, 0)] if len(decoded.data) >= 4 else [])


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Chimera native ISA codec and object tool")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assemble", help="assemble one instruction to hex")
    a.add_argument("--arch", choices=sorted(BACKENDS), required=True)
    a.add_argument("instruction", nargs="+")
    d = sub.add_parser("disassemble", help="disassemble hex bytes")
    d.add_argument("--arch", choices=sorted(BACKENDS), required=True)
    d.add_argument("hex")
    o = sub.add_parser("emit-object", help="write a valid demo native object")
    o.add_argument("--arch", choices=sorted(BACKENDS), default="riscv64")
    o.add_argument("--instruction", default="ADDI x1,x2,5")
    o.add_argument("--output", required=True)
    v = sub.add_parser("validate-object", help="strictly validate a native object")
    v.add_argument("path")
    v.add_argument("--arch")
    args = parser.parse_args()
    if args.cmd == "assemble":
        decoded = assemble(args.arch, " ".join(args.instruction))
        print(decoded.data.hex())
        print(decoded.text)
    elif args.cmd == "disassemble":
        decoded = disassemble(args.arch, bytes.fromhex(args.hex.replace("0x", "")))
        print(json.dumps(decoded.as_dict(), indent=2))
    elif args.cmd == "emit-object":
        Path(args.output).write_bytes(demo_object(args.arch, args.instruction))
        print(f"wrote {args.output}")
    else:
        obj = validate_object(Path(args.path).read_bytes(), args.arch)
        print(json.dumps({"arch": obj.arch, "abi": obj.abi_version,
                          "sections": [s.name for s in obj.sections],
                          "symbols": [s.name for s in obj.symbols],
                          "relocations": len(obj.relocations)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
