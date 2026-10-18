#!/usr/bin/env python3
"""Ensure ISA execution evidence names real unit tests without promoting conformance claims."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/"tools/isa/rv32-machine-tested-subset.json").read_text(encoding="utf-8"))
tests=(ROOT/"tools/isa/test_rv32_machine.py").read_text(encoding="utf-8")
machine=(ROOT/"tools/isa/rv32_machine.py").read_text(encoding="utf-8")
assert data["schema"]=="CHM-RV32-MACHINE-UNIT-TESTED-SUBSET-1"
for item in data["unit_tested"]:
 assert item["mnemonic"] in machine, f"listed instruction not referenced by machine implementation: {item['mnemonic']}"
 for test in item["tests"]:
  assert f"def {test}(" in tests, f"missing test evidence: {test}"
for item in data["expected_trap"]:
 for test in item["tests"]:
  assert f"def {test}(" in tests, f"missing trap test: {test}"
assert "full RV32I conformance" in data["explicitly_not_claimed"]
print("RV32 machine unit-tested subset evidence valid; no ISA conformance promotion performed.")
