#!/usr/bin/env python3
"""Fail-closed acceptance check for actual target-specific init userspace readiness."""
from pathlib import Path
import re
import sys

TARGETS={"live","installer","recovery"}
KERNEL_MARKER="[KRN ] KORONOS READY"
READY_RE=re.compile(r"USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)\b")

def main() -> int:
    if len(sys.argv)!=3 or sys.argv[1] not in TARGETS:
        print("usage: verify-userspace-handoff.py {live|installer|recovery} TRACE",file=sys.stderr)
        return 2
    target,trace_path=sys.argv[1],Path(sys.argv[2])
    if not trace_path.is_file():
        print(f"FAIL: trace not found: {trace_path}",file=sys.stderr);return 1
    trace=trace_path.read_text(encoding="utf-8",errors="replace")
    missing=[]
    if KERNEL_MARKER not in trace:missing.append("Koronos kernel readiness")
    matches=list(READY_RE.finditer(trace))
    if not matches:missing.append("actual init PID readiness marker")
    elif not any(m.group(1)==target and int(m.group(2))>0 for m in matches):
        missing.append(f"{target} userspace readiness with nonzero init PID")
    if missing:
        print("FAIL: missing "+", ".join(missing));return 1
    print(f"PASS: Koronos and {target} userspace ready with init PID")
    return 0
if __name__=="__main__":raise SystemExit(main())
