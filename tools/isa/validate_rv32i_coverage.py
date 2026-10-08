#!/usr/bin/env python3
"""Validate explicit ISA coverage claims; never infer conformance from implementation."""
import json
from pathlib import Path

PATH = Path(__file__).with_name("rv32i-coverage.json")
FIELDS = ("documented", "encoded", "decoded", "executed", "conformance-tested")

def main():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == "CHM-RV32I-COVERAGE-1"
    names = [item["mnemonic"] for item in data["instructions"]]
    assert len(names) == len(set(names)), "duplicate instruction coverage row"
    for item in data["instructions"]:
        for field in FIELDS:
            assert isinstance(item.get(field), bool), f"{item.get('mnemonic')}: missing boolean {field}"
        if item["conformance-tested"]:
            assert all(item[x] for x in ("documented", "encoded", "decoded", "executed"))
            assert data["official_architectural_tests"]["status"] == "pass"
            assert data["official_architectural_tests"]["integrated"] is True
    official = data["official_architectural_tests"]
    if official["status"] != "pass":
        assert not any(x["conformance-tested"] for x in data["instructions"]), "conformance cannot be claimed before official tests pass"
    for group in ("machine_features",):
        for name, item in data[group].items():
            for field in FIELDS:
                assert isinstance(item.get(field), bool), f"{name}: missing boolean {field}"
            if item["conformance-tested"]:
                assert official["status"] == "pass" and official["integrated"] is True
    for item in data["architecture_backends"]:
        for field in FIELDS:
            assert isinstance(item.get(field), bool), f"{item['architecture']}: missing boolean {field}"
        if item["conformance-tested"]:
            raise SystemExit(f"backend cannot be called conformant without backend-specific suites: {item['architecture']}")
    print(f"RV32I coverage manifest valid: {len(names)} instruction rows; official conformance status={official['status']}")
if __name__ == "__main__":
    main()
