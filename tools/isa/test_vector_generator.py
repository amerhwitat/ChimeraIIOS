#!/usr/bin/env python3
"""Generate deterministic/randomized operands for Chimera ISA tests.

This tool generates data only; instruction semantics remain defined by the
emulator/reference implementation.
"""
import argparse
import csv
import random

OPS = [
    ("ADD", "0x01", "Chimera-R8192"),
    ("MUL", "0x02", "Chimera-R8192"),
    ("XOR", "0x03", "Chimera-R8192"),
    ("SHL", "0x04", "Chimera-N"),
    ("MODEXP", "0x30", "Chimera-R8192"),
    ("NETSEND", "0x50", "Chimera-Hybrid"),
]
FIELDS = ["mnemonic", "opcode", "family", "rd", "rs", "rt", "imm", "addr", "length", "flags"]


def rand_hex(rng: random.Random, bits: int) -> str:
    return "0x" + f"{rng.getrandbits(bits):0{bits // 4}X}"


def row(rng: random.Random, op):
    mnemonic, opcode, family = op
    out = {key: "" for key in FIELDS}
    out.update(mnemonic=mnemonic, opcode=opcode, family=family)
    if mnemonic in {"ADD", "MUL", "XOR"}:
        out.update(rd=rand_hex(rng, 8192), rs=rand_hex(rng, 8192), rt=rand_hex(rng, 8192))
    elif mnemonic == "SHL":
        out.update(rd=rand_hex(rng, 8192), rs=rand_hex(rng, 8192), imm=str(rng.randrange(8192)))
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
    args = parser.parse_args()
    if args.count < 0:
        parser.error("count must be non-negative")
    rng = random.Random(args.seed)
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for _ in range(args.count):
            writer.writerow(row(rng, rng.choice(OPS)))


if __name__ == "__main__":
    main()
