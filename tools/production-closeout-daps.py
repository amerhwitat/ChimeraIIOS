#!/usr/bin/env python3
"""Fail-closed production closeout gate for Koronos target acceptance evidence.

The evidence file is supplied by CI after the final ISO boot tests. This checker
never runs tests or manufactures evidence; missing, stale, candidate-only, or
internally inconsistent evidence is a release blocker.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARE = ("bios", "uefi")
CASE_IDS = tuple(f"{target}-{firmware}" for target in TARGETS for firmware in FIRMWARE)
HEX256 = re.compile(r"^[0-9a-fA-F]{64}$")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_evidence(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["top-level evidence must be a JSON object"]

    cases = data.get("cases")
    if not isinstance(cases, dict):
        return ["cases must be an object keyed by target-firmware"]
    for case_id in CASE_IDS:
        case = cases.get(case_id)
        if not isinstance(case, dict):
            errors.append(f"{case_id}: missing case evidence")
            continue
        if case.get("status") != "PASS":
            errors.append(f"{case_id}: status must be PASS, got {case.get('status')!r}")
        if not case.get("production_iso") or not nonempty(case.get("production_iso")):
            errors.append(f"{case_id}: missing production_iso artifact identity")
        if not isinstance(case.get("iso_sha256"), str) or not HEX256.fullmatch(case["iso_sha256"]):
            errors.append(f"{case_id}: iso_sha256 must be a 64-character SHA-256 hex digest")
        if not nonempty(case.get("raw_trace")):
            errors.append(f"{case_id}: missing raw_trace artifact/path")
        if case.get("cpl3_syscall_ack") is not True:
            errors.append(f"{case_id}: no verified CPL3-originated syscall acknowledgement")
        if case.get("process_visible_rootfs") is not True:
            errors.append(f"{case_id}: process-visible rootfs/VFS mount not proven")
        if case.get("rootfs_file_syscalls_verified") is not True:
            errors.append(f"{case_id}: process-visible rootfs OPEN/READ/CLOSE was not verified from ring 3")
        if not nonempty(case.get("rootfs_file_syscalls_evidence")):
            errors.append(f"{case_id}: missing raw evidence for rootfs OPEN/READ/CLOSE")
        if case_id.startswith(("live-", "recovery-")):
            if case.get("tmpfs_mutation_verified") is not True:
                errors.append(f"{case_id}: writable tmpfs create/write/read/truncate/unlink was not verified")
            if not nonempty(case.get("tmpfs_mutation_evidence")):
                errors.append(f"{case_id}: missing raw evidence for writable tmpfs operations")
        syscall_pid = case.get("syscall_pid")
        ready_pid = case.get("readiness_pid")
        if not isinstance(syscall_pid, int) or isinstance(syscall_pid, bool) or syscall_pid <= 0:
            errors.append(f"{case_id}: syscall_pid must be a positive kernel-owned PID")
        if not isinstance(ready_pid, int) or isinstance(ready_pid, bool) or ready_pid <= 0:
            errors.append(f"{case_id}: readiness_pid must be a positive kernel-owned PID")
        if isinstance(syscall_pid, int) and not isinstance(syscall_pid, bool) and isinstance(ready_pid, int) and not isinstance(ready_pid, bool) and syscall_pid != ready_pid:
            errors.append(f"{case_id}: syscall PID and readiness PID do not match")

    requirements = (
        ("aurora_handoff", ("status", "evidence"), "PASS"),
        ("installer_persistence", ("status", "write_verified", "cold_reboot_verified", "readback_verified", "evidence"), "PASS"),
        ("recovery_repair", ("status", "repair_verified", "postcondition_verified", "evidence"), "PASS"),
        ("smp", ("status", "ap_startup_verified", "overlapping_execution_verified", "evidence"), "PASS"),
    )
    for name, fields, expected_status in requirements:
        section = data.get(name)
        if not isinstance(section, dict):
            errors.append(f"{name}: missing evidence object")
            continue
        if section.get("status") != expected_status:
            errors.append(f"{name}: status must be {expected_status}")
        for field in fields:
            if field == "status":
                continue
            value = section.get(field)
            if field.endswith("_verified"):
                if value is not True:
                    errors.append(f"{name}: {field} must be true")
            elif not nonempty(value):
                errors.append(f"{name}: missing {field}")
        if name == "smp":
            cpu_ids = section.get("cpu_ids")
            if not isinstance(cpu_ids, list) or len({v for v in cpu_ids if isinstance(v, int) and not isinstance(v, bool)}) < 2:
                errors.append("smp: cpu_ids must prove execution on at least two distinct CPUs")

    if data.get("candidate_smoke_substituted") is True:
        errors.append("candidate smoke evidence cannot substitute for production ISO acceptance")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="CI-produced production acceptance evidence JSON")
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: cannot read valid evidence JSON: {exc}", file=sys.stderr)
        return 2
    errors = check_evidence(data)
    if errors:
        print("PRODUCTION CLOSEOUT: BLOCKED")
        for error in errors:
            print(f" - {error}")
        return 1
    print("PRODUCTION CLOSEOUT: PASS — all six production cases and independent runtime gates have evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
