#!/usr/bin/env python3
"""Validate the six-case evidence contract only; does not prove any boot passed."""
import json
from pathlib import Path

data = json.loads((Path(__file__).resolve().parent / "boot" / "six_case_acceptance_contract.json").read_text())
assert data["schema"] == "CHM-OS-PRODUCTION-SIX-CASE-1"
assert data["status"] == "contract-only"
assert len(data["cases"]) == 6
assert {case["target"] for case in data["cases"]} == {"live", "installer", "recovery"}
assert {case["firmware"] for case in data["cases"]} == {"bios", "uefi"}
assert len({case["id"] for case in data["cases"]}) == 6
assert len(data["required_followups"]) >= 4
for case in data["cases"]:
    assert case["status"] == "NOT_RUN"
    assert case["evidence"]["init_pid"] is None
    assert case["evidence"]["syscall_cpl"] is None
    assert case["evidence"]["iso_sha256"] is None
print("PASS: contract schema valid; all six production cases remain NOT_RUN")
