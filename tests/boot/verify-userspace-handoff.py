#!/usr/bin/env python3
"""Fail-closed acceptance check for a real target-specific init userspace handoff.

The entry acknowledgement must be emitted by the syscall/exception entry path
after it has established that the originating context was executing at CPL 3.
A pre-transition kernel log line is not evidence of user-mode execution.
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
BLOCKED_MARKERS = (
    "NATIVE INIT BLOCKED:",
    "NATIVE INIT BLOCKED",
    "readiness withheld",
    "persistent services unavailable",
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
    entries = list(ENTRY_RE.finditer(trace))
    ready = list(READY_RE.finditer(trace))
    if kernel_at < 0:
        print("FAIL: missing Koronos kernel readiness")
        return 1
    valid_entries = [entry for entry in entries
                     if entry.group(1) == target and kernel_at < entry.start()]
    if not valid_entries:
        if not entries:
            print("FAIL: missing user-originated init syscall acknowledgement (CPL 3)")
        else:
            print(f"FAIL: no post-kernel CPL 3 init acknowledgement for requested target={target}")
        return 1
    if not ready:
        if any(marker in trace for marker in BLOCKED_MARKERS):
            print(f"FAIL: CPL 3 init entry observed for target={target}, but native init explicitly withheld readiness because required services are unavailable")
        else:
            print(f"FAIL: CPL 3 init entry observed for target={target}, but no actual USERSPACE READY PID marker; inspect init exit and service diagnostics")
        return 1
    for entry in valid_entries:
        for marker in ready:
            if (marker.group(1) == target and marker.group(2) == entry.group(2)
                    and entry.start() < marker.start()):
                print(f"PASS: target={target} init entered user mode and reported readiness with a consistent PID")
                return 0
    print("FAIL: expected ordered kernel-ready -> matching target/PID CPL 3 acknowledgement -> userspace-ready markers for target=" + target)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
