#!/usr/bin/env python3
"""Validate Chimera II OS ISA.csv schema and required architecture metadata."""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CSV = ROOT / "ISA.csv"
REQUIRED = {
    "architecture", "style", "mnemonic", "syntax", "binary_encoding",
    "hex_encoding", "operands", "optional_operands", "notes"
}
ARCHES = {
    "x86-64/IA-32", "AArch64", "RISC-V RV32I/RV64I", "MIPS32",
    "Power ISA", "SPARC V8/V9", "Motorola 68000", "VAX"
}

def main():
    with CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or set(reader.fieldnames) != REQUIRED:
            raise SystemExit("ISA.csv schema mismatch")
        rows = list(reader)
    if len(rows) < 50:
        raise SystemExit("ISA.csv unexpectedly small")
    seen = {r["architecture"] for r in rows}
    missing = ARCHES - seen
    if missing:
        raise SystemExit(f"missing architecture families: {sorted(missing)}")
    for i, row in enumerate(rows, 2):
        for field in REQUIRED:
            if not row[field].strip():
                raise SystemExit(f"row {i}: empty {field}")
    print(f"validated {len(rows)} ISA entries across {len(seen)} architecture families")

if __name__ == "__main__":
    main()
