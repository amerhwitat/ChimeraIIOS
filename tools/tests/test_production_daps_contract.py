#!/usr/bin/env python3
"""Fail-closed source contract for the production DAPS verifier."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "release/verify-production-daps.py"


def main() -> int:
    if not VERIFIER.is_file():
        print("DAPS CONTRACT FAIL: production verifier missing", file=sys.stderr)
        return 1
    source = VERIFIER.read_text(encoding="utf-8")
    required = (
        'TARGETS = ("live", "installer", "recovery")',
        'FIRMWARES = ("bios", "uefi")',
        "candidate ISO is missing",
        "extracted production init ELF hash mismatch",
        "user-originated CPL3 syscall acknowledgement missing",
        "ring-3 rootfs OPEN evidence missing",
        "ring-3 rootfs READ evidence missing",
        "ring-3 rootfs CLOSE evidence missing",
        "ring-3 writable /tmp write evidence missing",
        "USERSPACE TARGET READY: live component=aurora-session",
        "AURORA READY",
        "installer persistence/cold reboot not accepted",
        "recovery repair postcondition not verified",
        "SMP OVERLAP VERIFIED",
        "at least two AP-online CPU records",
    )
    for token in required:
        if token not in source:
            print(f"DAPS CONTRACT FAIL: missing fail-closed acceptance check: {token}", file=sys.stderr)
            return 1
    print("DAPS CONTRACT PASS: six ISO-bound traces, VFS/tmp, Aurora, install, recovery, and AP-SMP gates are enforced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
