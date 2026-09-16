#!/usr/bin/env python3
"""Print ISA registry coverage counts."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    db = json.loads((ROOT / "isa/isa_database.json").read_text(encoding="utf-8"))
    classes = {row[0]: row[1] for row in db["architectures"]}
    forms = Counter(classes[row[0]] for row in db["instructions"])
    print(f"Architectures: {len(db['architectures'])}")
    print(f"Instruction forms: {len(db['instructions'])}")
    for name in ("RISC", "CISC", "EPIC", "custom"):
        print(f"{name}: {forms[name]}")
    print("By architecture:")
    for row in db["architectures"]:
        print(f"  {row[0]:16} {row[1]:7} {row[7]:3}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
