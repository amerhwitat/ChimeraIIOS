#!/usr/bin/env python3
"""Fail-closed acceptance check for a real target-specific init userspace handoff.

The syscall acknowledgement must originate from a validated CPL3 entry path.
The verifier treats the trace as a whole: duplicated, wrong-target, zero-PID,
out-of-order, or mismatched-PID markers are failures rather than ignorable noise.
"""
from pathlib import Path
import re
import sys

TARGETS = {"live", "installer", "recovery"}
KERNEL_MARKER = "[KRN ] KORONOS READY"
ENTRY_RE = re.compile(
    r"USER INIT SYSCALL: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b"
)
READY_RE = re.compile(
    r"USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b"
)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in TARGETS:
        print("usage: verify-userspace-handoff.py {live|installer|recovery} TRACE", file=sys.stderr)
        return 2
    target, trace_path = sys.argv[1], Path(sys.argv[2])
    if not trace_path.is_file():
        print(f"FAIL: trace not found: {trace_path}", file=sys.stderr)
        return 1
    trace = trace_path.read_text(encoding="utf-8", errors="replace")
    kernels = list(re.finditer(re.escape(KERNEL_MARKER), trace))
    entries = list(ENTRY_RE.finditer(trace))
    ready = list(READY_RE.finditer(trace))

    if len(kernels) != 1:
        print(f"FAIL: expected exactly one kernel-ready marker, found {len(kernels)}")
        return 1
    if len(entries) != 1:
        print(f"FAIL: expected exactly one nonzero user-originated init syscall acknowledgement, found {len(entries)}")
        return 1
    if len(ready) != 1:
        print(f"FAIL: expected exactly one nonzero userspace-ready marker, found {len(ready)}")
        return 1

    entry, marker = entries[0], ready[0]
    if entry.group(1) != target or marker.group(1) != target:
        print(f"FAIL: target mismatch: expected {target}, syscall={entry.group(1)}, ready={marker.group(1)}")
        return 1
    if entry.group(2) != marker.group(2):
        print(f"FAIL: PID mismatch: syscall={entry.group(2)}, ready={marker.group(2)}")
        return 1
    if not kernels[0].start() < entry.start() < marker.start():
        print("FAIL: required ordered sequence is kernel-ready -> user-originated init syscall -> userspace-ready")
        return 1

    print(f"PASS: target={target} entered user mode and reported readiness with PID {marker.group(2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
