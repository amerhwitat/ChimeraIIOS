#!/usr/bin/env python3
"""Static safety contract for the not-yet-context-switching Koronos scheduler.

This test does not claim that yielding is implemented. It enforces the safer
ABI behavior: a yield request must return ENOSYS until a real context switch
is integrated with the architecture entry/return path.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "kernel" / "core" / "syscall.cpp"
text = SOURCE.read_text(encoding="utf-8")

yield_positions = [m.start() for m in re.finditer(r"case CHM_SYS_YIELD:", text)]
if len(yield_positions) != 2:
    raise AssertionError(f"expected two YIELD dispatch sites, found {len(yield_positions)}")


def body_at(start: int) -> str:
    end = text.find("case CHM_SYS_TIME_TICKS:", start)
    if end < 0:
        raise AssertionError("missing TIME_TICKS case after YIELD")
    return text[start:end]


compat, native = (body_at(pos) for pos in yield_positions)
if "chimera_sched_yield" in text:
    raise AssertionError("callback-only scheduler yield must not be called")
if not re.search(r"\*return_value\s*=\s*error_value\(\)", compat):
    raise AssertionError("compatibility YIELD must return ENOSYS")
if "return static_cast<uint64_t>(-38ll);" not in native:
    raise AssertionError("native YIELD must return ENOSYS")
if "return 0;" in native:
    raise AssertionError("native YIELD must not report false success")

print("PASS: YIELD remains ENOSYS until real context switching is implemented")
