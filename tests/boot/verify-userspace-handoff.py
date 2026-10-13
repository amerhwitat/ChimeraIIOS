#!/usr/bin/env python3
"""Fail-closed acceptance check for Koronos user-mode init handoff traces."""
from pathlib import Path
import sys

TARGET_MARKERS = {
    "live": "USERSPACE READY: live",
    "installer": "USERSPACE READY: installer",
    "recovery": "USERSPACE READY: recovery",
}
KERNEL_MARKER = "[KRN ] KORONOS READY"
# This string is emitted by the native init ELF through int 0x80 from CPL3,
# not by the kernel's generic bootstrap logging path.
INIT_MARKER = "[USER] Ring-3 Chimera init entered successfully; userspace handoff verified"

def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in TARGET_MARKERS:
        print("usage: verify-userspace-handoff.py {live|installer|recovery} TRACE", file=sys.stderr)
        return 2
    target, trace_path = sys.argv[1], Path(sys.argv[2])
    if not trace_path.is_file():
        print(f"FAIL: trace not found: {trace_path}", file=sys.stderr)
        return 1
    trace = trace_path.read_text(encoding="utf-8", errors="replace")
    missing = []
    if KERNEL_MARKER not in trace:
        missing.append("Koronos kernel readiness")
    if INIT_MARKER not in trace:
        missing.append("native init ELF ring-3 execution marker")
    if TARGET_MARKERS[target] not in trace:
        missing.append(f"{target} userspace readiness marker")
    if missing:
        print("FAIL: missing " + ", ".join(missing))
        return 1
    print(f"PASS: Koronos, native init ELF ring-3 execution, and {target} userspace readiness verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
