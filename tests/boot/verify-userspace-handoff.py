#!/usr/bin/env python3
"""Fail-closed acceptance check for a persistent target-specific Koronos PID 1.

The entry acknowledgement must be emitted by the syscall/exception entry path
after it has established that the originating context was executing at CPL 3.
A readiness line alone is not proof of persistence; require a kernel-verified ACTIVE marker.
"""
from pathlib import Path
import re
import sys

ACTIVE_RE = re.compile(
    r"KORONOS PID1 ACTIVE: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b"
)
TERMINAL_RE = re.compile(
    r"(?:Target userspace init emitted its own readiness handshake and exited cleanly|"
    r"in-kernel PIT deadline expired|userspace init exited nonzero|"
    r"userspace init exited before its target-specific USERSPACE READY handshake|"
    r"\[\s*RUN\s*\]\s*(?:ERROR|FATAL)\s*:|"
    r"KORONOS\s+PANIC\s*:|kernel\s+panic\s*:)",
    re.IGNORECASE,
)

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
    missing = []
    kernel_at = trace.find(KERNEL_MARKER)
    if kernel_at < 0:
        missing.append("Koronos kernel readiness")
    entries = list(ENTRY_RE.finditer(trace))
    if not entries:
        missing.append("user-originated init syscall acknowledgement (CPL 3)")
    ready = list(READY_RE.finditer(trace))
    if not ready:
        missing.append("actual init PID readiness marker")
    if missing:
        print("FAIL: missing " + ", ".join(missing))
        return 1
    active = list(ACTIVE_RE.finditer(trace))
    if not active:
        print("FAIL: missing kernel-verified persistent PID1 ACTIVE marker")
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
                    if TERMINAL_RE.search(trace, live_pid.end()):
                        print("FAIL: PID 1 terminated or was aborted after readiness")
                        return 1
                    print(f"PASS: target={target} has a kernel-verified resident PID 1 with matching nonzero PID")
                    return 0
    print("FAIL: expected ordered kernel-ready -> CPL3 syscall -> userspace-ready -> kernel PID1 ACTIVE markers for target=" + target + " with the same nonzero PID")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
