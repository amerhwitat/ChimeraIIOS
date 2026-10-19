#!/usr/bin/env python3
"""Static six-case contract test. This does not execute QEMU or certify a boot."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent / "boot" / "six_case_acceptance_contract.json"
d=json.loads(p.read_text(encoding="utf-8"))
assert d["schema"]=="CHM-OS-PRODUCTION-SIX-CASE-1"
assert d["status"]=="contract-only"
assert len(d["cases"])==6
assert {c["target"] for c in d["cases"]}=={"live","installer","recovery"}
assert {c["firmware"] for c in d["cases"]}=={"bios","uefi"}
for c in d["cases"]:
    assert c["status"]=="NOT_RUN"
    assert c["evidence"]["init_pid"] is None
    assert c["evidence"]["syscall_cpl"] is None
print("PASS: evidence contract schema only; all six runtime cases remain NOT_RUN")
