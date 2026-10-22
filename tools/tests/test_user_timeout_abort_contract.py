#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTERRUPT = (ROOT / "kernel/core/interrupt.cpp").read_text()
SYSCALL = (ROOT / "kernel/core/syscall.cpp").read_text()
ENTRY = (ROOT / "kernel/arch/x86_64/user_entry.asm").read_text()

assert "((saved[17] & 3u) == 3u)" in INTERRUPT
assert "koronos_user_timeout_abort_irq();" in INTERRUPT
assert "user_timeout_expired = 1;" in INTERRUPT
assert "koronos_user_timeout_pending()) koronos_user_timeout_abort();" in SYSCALL
irq_body = ENTRY.split("koronos_user_timeout_abort_irq:", 1)[1].split("koronos_user_timeout_abort:", 1)[0]
syscall_body = ENTRY.split("koronos_user_timeout_abort:", 1)[1]
assert "swapgs" not in irq_body, "CPL3 IRQ abort must not swap GS twice"
assert "swapgs" in syscall_body, "SYSCALL abort must restore GS after syscall entry swapgs"
assert "pushfq; popq %0" in INTERRUPT and "if (saved_flags & (1ull << 9))" in INTERRUPT
print("user-timeout abort contract: PASS (CPL0 deferral, IRQ/syscall GS separation, IF restoration)")
