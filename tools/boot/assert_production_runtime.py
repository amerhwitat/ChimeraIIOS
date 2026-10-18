#!/usr/bin/env python3
"""Fail-closed production boot-log acceptance gate for Chimera II OS."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

TARGET_READY = {
    "live": r"\bLIVE READY\b",
    "installer": r"\bINSTALLER READY\b",
    "recovery": r"\bRECOVERY READY\b",
    "installed": r"\bINSTALLED DISK READY\b",
}
STALL_PATTERNS = (
    r"awaiting a supported userspace handoff",
    r"blocked handoff",
    r"production userspace handoff failed",
)

def validate_log(log: str, target: str, require_smp: bool = False) -> list[str]:
    errors: list[str] = []
    for pattern in STALL_PATTERNS:
        if re.search(pattern, log, re.IGNORECASE):
            errors.append(f"stall/failure diagnostic present: {pattern}")
    stages = [
        (r"KORONOS READY", "kernel-ready marker"),
        (rf"CHM_TARGET_SELECTED\s+target={re.escape(target)}\b", f"{target} target-selection marker"),
        (r"USERSPACE READY:\s*init pid=\d+", "userspace-originated init-ready marker"),
        (r"USERSPACE IO READY", "userspace I/O/syscall marker"),
        (TARGET_READY[target], f"{target} runtime-ready marker"),
    ]
    if target in ("live", "installed"):
        stages.append((r"AURORA READY", "Aurora-ready marker"))
    cursor = 0
    for pattern, description in stages:
        match = re.search(pattern, log[cursor:], re.IGNORECASE)
        if not match:
            errors.append(f"missing or out-of-order {description}")
            continue
        cursor += match.end()
    if require_smp and not re.search(r"\bSMP READY\s+cpus=(?:[2-9]|[1-9]\d+)\b", log, re.IGNORECASE):
        errors.append("missing SMP READY marker proving at least two CPUs")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path, help="captured serial/debugcon runtime log")
    parser.add_argument("--target", required=True, choices=sorted(TARGET_READY))
    parser.add_argument("--require-smp", action="store_true", help="require evidence of at least two CPUs")
    args = parser.parse_args()
    try:
        log = args.log.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"FAIL: cannot read runtime log: {exc}", file=sys.stderr)
        return 2
    errors = validate_log(log, args.target, args.require_smp)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: production {args.target} runtime markers are ordered and complete")
    if args.require_smp:
        print("PASS: SMP marker reports at least two CPUs")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
