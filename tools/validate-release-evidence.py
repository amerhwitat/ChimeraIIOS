#!/usr/bin/env python3
"""Fail-closed production release evidence validator for native Koronos."""
import argparse, json, re, sys
from pathlib import Path

def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[RELEASE-GATE] cannot read {path}: {exc}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capabilities", default="docs/validation/capability-evidence.json")
    parser.add_argument("--handoff", default="build/acceptance/native-userspace-handoff.json")
    parser.add_argument("--smp", default="build/acceptance/real-smp.json")
    args = parser.parse_args()
    caps = load(args.capabilities)
    statuses = {item.get("id"): item.get("status") for item in caps.get("capabilities", [])}
    required = {"live-userspace": "userspace-ready",
                "native-vfs-syscalls": "conformance-tested",
                "real-smp": "conformance-tested"}
    failures = {key: {"required": value, "actual": statuses.get(key)}
                for key, value in required.items() if statuses.get(key) != value}
    if failures:
        raise SystemExit("[RELEASE-GATE] capability promotion missing: " + json.dumps(failures, sort_keys=True))
    handoff = load(args.handoff)
    if handoff.get("schema") != "CHIMERA-NATIVE-USERSPACE-HANDOFF-1" or handoff.get("status") != "accepted":
        raise SystemExit("[RELEASE-GATE] native handoff evidence is not accepted")
    if handoff.get("cpl3_syscall_ack") is not True or int(handoff.get("init_pid", 0)) <= 0:
        raise SystemExit("[RELEASE-GATE] CPL3 syscall acknowledgement and nonzero init PID are required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(handoff.get("iso_sha256", ""))):
        raise SystemExit("[RELEASE-GATE] immutable ISO SHA-256 is required")
    cases = {(case.get("edition"), case.get("firmware")) for case in handoff.get("cases", [])
             if case.get("status") == "passed"}
    expected = {(edition, firmware) for edition in ("Live", "Installer", "Recovery")
                for firmware in ("BIOS", "UEFI")}
    if not expected.issubset(cases):
        raise SystemExit("[RELEASE-GATE] all six Live/Installer/Recovery x BIOS/UEFI cases must pass")
    smp = load(args.smp)
    if smp.get("schema") != "CHIMERA-REAL-SMP-1" or smp.get("status") != "accepted":
        raise SystemExit("[RELEASE-GATE] real SMP evidence is not accepted")
    if int(smp.get("cpu_count", 0)) < 2 or not all(
        smp.get(key) is True for key in ("ap_startup", "concurrent_execution", "ipi_synchronization")
    ):
        raise SystemExit("[RELEASE-GATE] AP startup, >=2 CPUs, concurrent execution and IPI synchronization are required")
    print("[RELEASE-GATE] native Koronos production evidence accepted")
    return 0

if __name__ == "__main__":
    sys.exit(main())
