#!/usr/bin/env python3
"""Prevent syscall stubs from pretending PID/exit lifecycle support exists."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "kernel/core/syscall.cpp").read_text(encoding="utf-8")

# Until current-process binding and teardown are wired into the dispatcher,
# GETPID and EXIT must fail closed rather than emit misleading success values.
assert "case CHM_SYS_GETPID:" in SOURCE
assert "case CHM_SYS_EXIT:" in SOURCE
assert "case CHM_SYS_EXIT_GROUP:" in SOURCE
block = SOURCE.split("case CHM_SYS_GETPID:", 1)[1].split("case CHM_SYS_YIELD:", 1)[0]
assert "++g_rejected;" in block
assert "*return_value = error_value();" in block
assert "return -1;" in block
assert "*return_value = 1u;" not in SOURCE
assert "*return_value = 0;" not in block
print("syscall process-lifecycle fail-closed contract: PASS")
