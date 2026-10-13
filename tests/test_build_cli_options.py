#!/usr/bin/env python3
"""Regression test for documented online ISA catalog refresh CLI aliases."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
script = (root / "build-chimera-iso.sh").read_text(encoding="utf-8")
assert "--refresh-online-catalogs|--refresh-isa-catalog)" in script, (
    "the ISO builder must accept both documented catalog refresh options"
)
assert "--refresh-online-catalogs, --refresh-isa-catalog" in script, (
    "help output must document the ISA refresh alias"
)
print("ISO builder catalog refresh aliases: PASS")
