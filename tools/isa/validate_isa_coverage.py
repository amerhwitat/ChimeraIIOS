#!/usr/bin/env python3
"""Validate ISA coverage manifests without upgrading inventory to implementation."""
import json
from pathlib import Path

FIELDS = ("documented", "encoded", "decoded", "executed", "conformance-tested")
ROOT = Path(__file__).resolve().parent

def validate(path, schema, row_groups):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("schema") == schema, f"{path.name}: unsupported schema"
    official = data["official_architectural_tests"]
    assert official["status"] in {"not-run", "running", "fail", "pass"}
    if official["status"] != "pass":
        assert official["conformance_claim"] is False, f"{path.name}: conformance claim without passing suite"
    if official["status"] == "pass":
        assert official["integrated"] is True, f"{path.name}: suite is not integrated"
    count = 0
    for group_name in row_groups:
        rows = data[group_name]
        if isinstance(rows, dict):
            rows = [{"name": name, **row} for name, row in rows.items()]
        seen = set()
        for row in rows:
            name = row.get("mnemonic", row.get("name", row.get("architecture", "")))
            assert name and name not in seen, f"{path.name}: missing/duplicate row name {name!r}"
            seen.add(name)
            for field in FIELDS:
                assert isinstance(row.get(field), bool), f"{path.name}: {name}: missing boolean {field}"
            if row["conformance-tested"]:
                assert all(row[x] for x in ("documented", "encoded", "decoded", "executed")), f"{name}: conformance requires all prior stages"
                assert official["status"] == "pass" and official["integrated"] is True and official["conformance_claim"] is True, f"{name}: no passing integrated suite"
            count += 1
    print(f"{path.name}: valid; {count} rows; official conformance={official['status']}")

def main():
    validate(ROOT / "rv32i-coverage.json", "CHM-RV32I-COVERAGE-1", ("instructions", "machine_features", "architecture_backends"))
    validate(ROOT / "cisc-coverage.json", "CHM-CISC-COVERAGE-1", ("instruction_groups", "cpu_profiles", "machine_features", "backends", "non_cisc_backends"))

if __name__ == "__main__":
    main()
