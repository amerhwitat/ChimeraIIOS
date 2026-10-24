#!/usr/bin/env python3
"""Fail-closed production DAPS gate for one ISO and six target/firmware traces.

Evidence must be produced by the real boot/test harness, never synthesized by
this validator. Missing fields, an ISO digest mismatch, candidate-probe traces,
or kernel-authored readiness markers are hard failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CASES = tuple(
    (target, firmware)
    for target in ("live", "installer", "recovery")
    for firmware in ("bios", "uefi")
)
BASE_MOUNTS = {"/proc", "/sys", "/dev", "/run", "/tmp"}
SERVICES = {
    "live": {"device-manager", "filesystem", "network", "logging",
             "process-supervisor", "session-manager"},
    "installer": {"device-manager", "filesystem", "storage-discovery",
                  "network", "logging", "process-supervisor",
                  "installer-transaction"},
    "recovery": {"device-manager", "filesystem", "storage-discovery",
                 "logging", "process-supervisor", "recovery-manager"},
}
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class GateError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"{path}: cannot read valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{path}: evidence root must be a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_case(path: Path, target: str, firmware: str, iso_sha: str) -> None:
    e = load_json(path)
    prefix = f"{target}/{firmware}"
    require(e.get("target") == target, f"{prefix}: target identity mismatch")
    require(e.get("firmware") == firmware, f"{prefix}: firmware identity mismatch")
    digest = e.get("iso_sha256")
    require(isinstance(digest, str) and HEX_SHA256.fullmatch(digest) is not None,
            f"{prefix}: missing/invalid iso_sha256")
    require(digest == iso_sha, f"{prefix}: trace ISO SHA-256 does not match tested ISO")
    require(e.get("ring3_init_syscall_ack") is True,
            f"{prefix}: missing real ring-3 init syscall acknowledgement")
    require(e.get("syscall_ack_origin") == "ring3-user-init",
            f"{prefix}: syscall acknowledgement is not attributed to ring-3 init")
    pid = e.get("userspace_pid")
    require(type(pid) is int and pid > 0, f"{prefix}: userspace PID must be a positive integer")
    require(e.get("userspace_pid_origin") == "kernel-owned-process-table",
            f"{prefix}: PID is not proven to come from the kernel process table")
    require(e.get("kernel_emitted_readiness_marker") is False,
            f"{prefix}: kernel-authored readiness marker is invalid evidence")
    require(e.get("candidate_probe_only") is not True,
            f"{prefix}: candidate probe is not production userspace evidence")
    require(e.get("target_service_health") is True,
            f"{prefix}: target services have not passed health checks")
    mounts = e.get("mounts")
    require(isinstance(mounts, list) and all(isinstance(x, str) for x in mounts)
            and BASE_MOUNTS.issubset(set(mounts)),
            f"{prefix}: required /proc, /sys, /dev, /run, /tmp mounts not proven")
    health = e.get("services")
    require(isinstance(health, dict), f"{prefix}: missing per-service health results")
    missing = sorted(name for name in SERVICES[target] if health.get(name) != "healthy")
    require(not missing, f"{prefix}: unhealthy/missing required services: {', '.join(missing)}")

    if target == "live":
        require(e.get("aurora_native_session") is True,
                f"{prefix}: native Aurora session not proven")
    elif target == "installer":
        for field in ("transaction_committed", "write_readback_verified",
                      "boot_entry_verified", "cold_reboot_passed",
                      "persistent_readback_passed"):
            require(e.get(field) is True, f"{prefix}: {field} not proven")
    else:
        require(e.get("repair_or_rollback_postconditions") is True,
                f"{prefix}: recovery repair/rollback postconditions not proven")


def check_smp(path: Path) -> None:
    e = load_json(path)
    ids = e.get("apic_ids")
    require(isinstance(ids, list) and len(ids) >= 2 and
            all(type(x) is int and x >= 0 for x in ids) and len(set(ids)) == len(ids),
            "SMP: need distinct BSP/AP APIC IDs from runtime evidence")
    ap_count = e.get("ap_workers_started")
    require(type(ap_count) is int and ap_count >= 1,
            "SMP: no application processor startup proven")
    require(e.get("overlapping_execution_observed") is True,
            "SMP: overlapping execution was not observed")
    completed = e.get("workers_completed")
    require(type(completed) is int and completed >= 2,
            "SMP: at least two concurrently scheduled workers must complete")
    require(e.get("simulated") is False,
            "SMP: simulated/sequential CPU execution is not acceptable evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path, help="exact ISO tested by the boot harness")
    parser.add_argument("--evidence-dir", required=True, type=Path,
                        help="directory containing live-bios.json ... recovery-uefi.json and smp.json")
    args = parser.parse_args()
    try:
        require(args.iso.is_file(), f"ISO does not exist: {args.iso}")
        iso_sha = sha256_file(args.iso)
        print(f"ISO SHA-256: {iso_sha}")
        for target, firmware in CASES:
            check_case(args.evidence_dir / f"{target}-{firmware}.json",
                       target, firmware, iso_sha)
            print(f"PASS: {target}/{firmware}")
        check_smp(args.evidence_dir / "smp.json")
        print("PASS: genuine AP-backed overlapping SMP")
        print("DAPS PASS: all six target/firmware cases and SMP evidence match this ISO")
        return 0
    except (GateError, OSError, TypeError, ValueError) as exc:
        print(f"DAPS BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
