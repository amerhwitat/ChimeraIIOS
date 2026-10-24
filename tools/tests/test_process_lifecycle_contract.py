#!/usr/bin/env python3
"""Static safety contract for the bounded process registry's terminal reaper."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "kernel/include/chimera/process.h"
SOURCE = ROOT / "kernel/core/process.cpp"
ADDRESS_SPACE = ROOT / "kernel/core/address_space.cpp"
LOADER_HEADER = ROOT / "kernel/include/chimera/process_loader.h"
LOADER_SOURCE = ROOT / "kernel/core/process_loader.cpp"
TARGET_SOURCE = ROOT / "kernel/core/target_launch.cpp"


def main() -> int:
    if not all(p.is_file() for p in (HEADER, SOURCE, ADDRESS_SPACE, LOADER_HEADER, LOADER_SOURCE, TARGET_SOURCE)):
        print("PROCESS LIFECYCLE FAIL: process registry source missing", file=sys.stderr)
        return 1
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    address_space = ADDRESS_SPACE.read_text(encoding="utf-8")
    loader_header = LOADER_HEADER.read_text(encoding="utf-8")
    loader = LOADER_SOURCE.read_text(encoding="utf-8")
    target = TARGET_SOURCE.read_text(encoding="utf-8")
    required_header = ("int chimera_process_mark_resources_released(uint32_t pid);",
        "int chimera_process_reap(uint32_t pid);",)
    required_source = (
        "if (state != CHIMERA_PROCESS_EXITED && state != CHIMERA_PROCESS_FAULTED)",
        "Never free a running, ready, blocked, or merely admitted process",
        "if (count == 0) return -5;",
        "if (!slots[i].resources_released) return -6;",
        "slots[i].resources_released = true;",
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
    required_address_space = (
        "static int destroy_locked(AddressSpace *space)",
        "space->poisoned = 1;",
        "&& !spaces[i].poisoned",
        "static int destroy_address_space(void *, void *opaque)",
    )
    required_loader_header = ("int (*destroy_address_space)(void *context, void *address_space);",)
    required_loader = ("==0 ? -14 : -17", "==0 ? -16 : -17", "==0 ? -15 : -17")
    required_target = (
        "const int destroy_rc = ops->destroy_address_space(nullptr,loaded.address_space);",
        "chimera_process_mark_resources_released(exited_pid)",
        "chimera_process_reap(exited_pid)",
        "process teardown incomplete; address space or descriptors were not proven released",
    )
    for label, body, tokens in (
        ("address-space quarantine", address_space, required_address_space),
        ("loader teardown ABI", loader_header, required_loader_header),
        ("loader rollback", loader, required_loader),
        ("target teardown", target, required_target),
    ):
        for token in tokens:
            if token not in body:
                print(f"PROCESS LIFECYCLE FAIL: missing {label} contract: {token}", file=sys.stderr)
                return 1
    print("PROCESS LIFECYCLE PASS: only terminal process records can be reaped; PIDs are not recycled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
