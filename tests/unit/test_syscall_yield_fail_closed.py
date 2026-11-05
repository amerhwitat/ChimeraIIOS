#!/usr/bin/env python3
"""Static safety contract for the not-yet-context-switching Koronos scheduler.

This test does not claim that yielding is implemented. It enforces the safer
ABI behavior: a yield request must return ENOSYS until a real context switch
is integrated with the architecture entry/return path.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "kernel" / "core" / "syscall.cpp"
text = SOURCE.read_text(encoding="utf-8")


def case_body(label: str, next_label: str) -> str:
    start = text.find(label)
    if start < 0:
        raise AssertionError(f"missing syscall case: {label}")
    end = text.find(next_label, start + len(label))
    if end < 0:
        raise AssertionError(f"missing following case after: {label}")
    return text[start:end]


compat = case_body(
    "case CHM_SYS_YIELD:",
    "case CHM_SYS_TIME_TICKS:",
)
native = case_body(
    "case CHM_SYS_YIELD:",
    "case CHM_SYS_TIME_TICKS:",
)
# The first switch is the compatibility dispatcher; the second is the
# process-bound native dispatcher. Both must fail closed in the current tree.
if "chimera_sched_yield" in text:
    raise AssertionError("callback-only scheduler yield must not be called")
if not re.search(r"\*return_value\s*=\s*error_value\(\)", compat):
    raise AssertionError("compatibility YIELD must return ENOSYS")
if "return static_cast<uint64_t>(-38ll);" not in native:
    raise AssertionError("native YIELD must return ENOSYS")
if "return 0;" in native:
    raise AssertionError("native YIELD must not report false success")

print("PASS: YIELD remains ENOSYS until real context switching is implemented")
