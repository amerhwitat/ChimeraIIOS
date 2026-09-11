#!/usr/bin/env python3
"""Generate deterministic/randomized operands and golden scalar vectors for Chimera ISA tests."""
import argparse
import csv
import random

OPS = [
    ("ADD", "0x01", "Chimera-R8192"),
    ("SUB", "0x02", "Chimera-R8192"),
    ("MUL", "0x03", "Chimera-R8192"),
    ("DIV", "0x04", "Chimera-R8192"),
    ("AND", "0x05", "Chimera-R8192"),
    ("OR", "0x06", "Chimera-R8192"),
    ("XOR", "0x07", "Chimera-R8192"),
    ("SHL", "0x08", "Chimera-R8192"),
    ("SHR", "0x09", "Chimera-R8192"),
    ("MODEXP", "0x0E", "Chimera-R8192"),
    ("NETSEND", "0x30", "Chimera-Hybrid"),
]
FIELDS = ["mnemonic", "opcode", "family", "rd", "rs", "rt", "imm", "addr", "length", "flags", "expected"]
MASK64 = (1 << 64) - 1


def rand_hex(rng: random.Random, bits: int) -> str:
    return "0x" + f"{rng.getrandbits(bits):0{bits // 4}X}"


def scalar_expected(mnemonic, a, b, imm=None):
    if mnemonic == "ADD":
        return (a + b) & MASK64
    if mnemonic == "SUB":
        return (a - b) & MASK64
    if mnemonic == "MUL":
        return (a * b) & MASK64
    if mnemonic == "DIV":
        return 0 if b == 0 else a // b
    if mnemonic == "AND":
        return a & b
    if mnemonic == "OR":
        return a | b
    if mnemonic == "XOR":
        return a ^ b
    if mnemonic == "SHL":
        return (a << (imm % 64)) & MASK64
    if mnemonic == "SHR":
        return a >> (imm % 64)
    raise ValueError(mnemonic)


def row(rng: random.Random, op, golden=False):
    mnemonic, opcode, family = op
    out = {key: "" for key in FIELDS}
    out.update(mnemonic=mnemonic, opcode=opcode, family=family)
    if mnemonic in {"ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR"}:
        a = rng.getrandbits(64)
        b = rng.getrandbits(64)
        out.update(rd=rand_hex(rng, 8192), rs=f"0x{a:016X}", rt=f"0x{b:016X}")
        if golden:
            out["expected"] = f"0x{scalar_expected(mnemonic, a, b):016X}"
    elif mnemonic in {"SHL", "SHR"}:
        a = rng.getrandbits(64)
        imm = rng.randrange(64)
        out.update(rd=rand_hex(rng, 8192), rs=f"0x{a:016X}", imm=str(imm))
        if golden:
            out["expected"] = f"0x{scalar_expected(mnemonic, a, 0, imm):016X}"
    elif mnemonic == "MODEXP":
        out.update(rd=rand_hex(rng, 8192), rs=rand_hex(rng, 8192), imm=rand_hex(rng, 64))
    elif mnemonic == "NETSEND":
        out.update(addr=rand_hex(rng, 64), length=str(rng.randint(64, 1500)), flags="0")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="test_vectors.csv")
    parser.add_argument("count", nargs="?", type=int, default=100)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--golden", action="store_true", help="include deterministic scalar expected results")
    args = parser.parse_args()
    if args.count < 0:
        parser.error("count must be non-negative")
    rng = random.Random(args.seed)
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for _ in range(args.count):
            writer.writerow(row(rng, rng.choice(OPS), golden=args.golden))


if __name__ == "__main__":
    main()
