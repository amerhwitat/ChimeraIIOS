#!/usr/bin/env python3
"""Guard the freestanding Koronos init payload against Linux/native syscall-ID mixups."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
COMMON = (ROOT / "kernel/targets/init_common.h").read_text()
COMPAT = (ROOT / "kernel/core/compat.cpp").read_text()

expected = {
    "LINUX_X86_64_SYS_WRITE": (1, 9),
    "LINUX_X86_64_SYS_GETPID": (39, 2),
    "LINUX_X86_64_SYS_EXIT": (60, 1),
}
for macro, (linux_number, canonical_id) in expected.items():
    define = re.search(rf"^#define\s+{macro}\s+(\d+)\s*$", COMMON, re.M)
    assert define and int(define.group(1)) == linux_number, (
        f"{macro} must use Linux x86-64 syscall number {linux_number}"
    )
    mapping = re.search(
        rf"case\s+{linux_number}\s*:\s*return\s+{canonical_id}\s*;",
        COMPAT,
    )
    assert mapping, (
        f"compat.cpp must translate Linux syscall {linux_number} "
        f"to Chimera semantic ID {canonical_id}"
    )

assert not re.search(r"\bCHM_SYS_[A-Z0-9_]+\b", COMMON), (
    "native semantic syscall IDs must not be passed directly to Linux SYSCALL"
)
SMOKE = (ROOT / "kernel/tests/user_init_smoke.c").read_text()
assert re.search(r'number\s+__asm__\("rax"\)\s*=\s*39\s*;.*Linux x86-64 getpid', SMOKE), (
    "ring-3 smoke payload must use Linux x86-64 getpid=39, not Chimera semantic ID 2"
)
assert re.search(r'number\s*=\s*1\s*;\s*/\* Linux x86-64 write \*/', SMOKE), (
    "ring-3 smoke payload must use Linux x86-64 write=1"
)
assert re.search(r'number\s*=\s*60\s*;\s*/\* Linux x86-64 exit \*/', SMOKE), (
    "ring-3 smoke payload must use Linux x86-64 exit=60"
)

assert 'int $0x80' in COMMON, (
    "the CPL3-origin acknowledgement must still enter through the DPL3 INT 0x80 gate"
)
for target in ("live", "installer", "recovery"):
    source = (ROOT / f"kernel/targets/{target}_init.c").read_text()
    assert "init_getpid()" in source and "init_emit_readiness(pid)" in source
    assert "init_exit(0)" in source

print("native init syscall ABI contract: PASS")
