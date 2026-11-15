#!/usr/bin/env python3
"""Fail-closed acceptance check for a persistent target-specific Koronos PID 1.

A CPL3 syscall acknowledgement and a matching readiness write prove that an
ELF ran in userspace. They do not prove that PID 1 stayed alive. Production
acceptance therefore also requires a kernel-originated PID1 ACTIVE record
after readiness, and rejects process exit or timeout records.
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
# This line must be emitted by the kernel only after it has verified that the
# same target PID remains RUNNING after the target's service-init phase.
ACTIVE_RE = re.compile(
    r"KORONOS PID1 ACTIVE: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b"
)
TERMINAL_RE = re.compile(
    r"(?:Target userspace init emitted its own readiness handshake and exited cleanly|"
    r"userspace init exited before its target-specific USERSPACE READY handshake|"
    r"in-kernel PIT deadline expired|userspace init exited nonzero)"
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
    kernel_at = trace.find(KERNEL_MARKER)
    if kernel_at < 0:
        print("FAIL: missing Koronos kernel readiness")
        return 1

    entries = list(ENTRY_RE.finditer(trace))
    ready = list(READY_RE.finditer(trace))
    active = list(ACTIVE_RE.finditer(trace))
    if not entries:
        print("FAIL: missing user-originated init syscall acknowledgement (CPL 3)")
        return 1
    if not ready:
        print("FAIL: missing actual init PID readiness marker")
        return 1
    if not active:
        print("FAIL: missing kernel-verified persistent PID 1 active marker; a short-lived ELF probe is not a running userspace")
        return 1

    for entry in entries:
        if entry.group(1) != target or kernel_at >= entry.start():
            continue
        for marker in ready:
            if (marker.group(1) != target or marker.group(2) != entry.group(2)
                    or entry.start() >= marker.start()):
                continue
            for live_pid in active:
                if (live_pid.group(1) == target and live_pid.group(2) == entry.group(2)
                        and marker.start() < live_pid.start()):
                    terminal = TERMINAL_RE.search(trace, live_pid.end())
                    if terminal:
                        print("FAIL: PID 1 terminated or was aborted after its readiness marker")
                        return 1
                    print(f"PASS: target={target} has a kernel-verified persistent PID 1 with matching nonzero PID")
                    return 0

    print("FAIL: expected ordered kernel-ready -> CPL3 syscall -> userspace-ready -> persistent PID1-active markers for target=" + target + " with the same nonzero PID")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
