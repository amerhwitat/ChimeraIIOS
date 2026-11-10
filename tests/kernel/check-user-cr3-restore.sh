#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASM="$ROOT/kernel/arch/x86_64/user_entry.asm"
python3 - "$ASM" <<'PY'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
def body(label, end):
    start = s.index(label)
    stop = s.index(end, start)
    return s[start:stop]
enter = body("koronos_arch_enter_user:", ".bad_user_entry:")
exit_path = body("koronos_syscall_user_exit:", "koronos_fatal_cr3_restore:")
fatal = body("koronos_fatal_cr3_restore:", "; Called only by the dedicated IRQ0 stub")
timeout = body("koronos_user_timeout_abort:", "section .data")
assert "test rdi, 0xFFF" in enter, "entry must reject unaligned CR3 roots"
assert "cmp rdi, rax" in enter and "jae .bad_user_entry" in enter, "entry must reject roots outside the supported physical window"
assert "mov rax, cr3" in enter, "user entry must capture the actual active caller CR3"
assert "mov [rel koronos_cpu_syscall_state + 48], rax" in enter
for name, text in (("syscall exit", exit_path), ("timeout abort", timeout)):
    assert "mov rax, [rel koronos_cpu_syscall_state + 48]" in text, f"{name} must load the saved caller CR3"
    assert "test rax, 0xFFF" in text, f"{name} must reject an unaligned saved CR3"
    assert "jnz koronos_fatal_cr3_restore" in text, f"{name} must fail closed on an invalid saved CR3"
    assert "mov cr3, rax" in text, f"{name} must restore the saved caller CR3"
    assert "koronos_bootstrap_pml4" not in text, f"{name} must not assume the bootstrap CR3"
assert "cli" in fatal and "hlt" in fatal and "jmp koronos_fatal_cr3_restore" in fatal, "invalid restore must halt fail-closed"
print("PASS: CR3 entry validation, exact active-root preservation, and fail-closed syscall/timeout restoration")
PY
