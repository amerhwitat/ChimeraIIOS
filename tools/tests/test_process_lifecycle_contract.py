#!/usr/bin/env python3
"""Static safety contract for the bounded process registry's terminal reaper."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "kernel/include/chimera/process.h"
SOURCE = ROOT / "kernel/core/process.cpp"


def main() -> int:
    if not HEADER.is_file() or not SOURCE.is_file():
        print("PROCESS LIFECYCLE FAIL: process registry source missing", file=sys.stderr)
        return 1
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    required_header = ("int chimera_process_reap(uint32_t pid);",)
    required_source = (
        "if (state != CHIMERA_PROCESS_EXITED && state != CHIMERA_PROCESS_FAULTED)",
        "Never free a running, ready, blocked, or merely admitted process",
        "if (count == 0) return -5;",
        "slots[i] = {};",
        "--count;",
    )
    for token in required_header:
        if token not in header:
            print(f"PROCESS LIFECYCLE FAIL: missing header contract: {token}", file=sys.stderr)
            return 1
    for token in required_source:
        if token not in source:
            print(f"PROCESS LIFECYCLE FAIL: missing implementation contract: {token}", file=sys.stderr)
            return 1
    print("PROCESS LIFECYCLE PASS: only terminal process records can be reaped; PIDs are not recycled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
