#!/usr/bin/env python3
"""Validate Chimera II's normalized ISA registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "isa" / "isa_database.json"
WORLD = ROOT / "isa" / "world_architectures.json"


def main() -> int:
    db = json.loads(DB.read_text(encoding="utf-8"))
    world = json.loads(WORLD.read_text(encoding="utf-8"))
    arch_rows = db["architectures"]
    arch_ids = {row[0] for row in arch_rows}
    world_ids = {row["id"] for row in world["architecture_families"]}
    errors: list[str] = []

    if not world_ids <= arch_ids:
        errors.append(f"world registry references missing DB architectures: {sorted(world_ids - arch_ids)}")
    seen: set[tuple[str, str, str]] = set()
    for row in db["instructions"]:
        if len(row) != 8:
            errors.append(f"instruction row must have 8 columns: {row[:3]}")
            continue
        arch, mnemonic, form, operands, syntax, length_bits, value_bits, mask_bits = row
        key = (arch, mnemonic, form)
        if key in seen:
            errors.append(f"duplicate instruction form: {key}")
        seen.add(key)
        if arch not in arch_ids:
            errors.append(f"instruction references unknown architecture: {arch}")
        if not operands:
            errors.append(f"missing operands: {key}")
        if not isinstance(length_bits, int) or length_bits <= 0:
            errors.append(f"invalid instruction width: {key}")
        if len(value_bits) != length_bits or len(mask_bits) != length_bits:
            errors.append(f"binary width mismatch: {key}")
        if set(value_bits) - set("01") or set(mask_bits) - set("01"):
            errors.append(f"non-binary encoding: {key}")
        if arch.startswith("chimera-") and arch not in {"chimera-c8192", "chimera-r8192"}:
            errors.append(f"unknown Chimera architecture: {arch}")
    if errors:
        print("ISA registry validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"ISA registry validation PASSED: {len(arch_rows)} architectures, {len(db['instructions'])} instruction forms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
