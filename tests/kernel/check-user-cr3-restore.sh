#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASM="$ROOT/kernel/arch/x86_64/user_entry.asm"
python3 - "$ASM" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
def body(label, end):
    start=s.index(label)
    stop=s.index(end,start)
    return s[start:stop]
enter=body("koronos_arch_enter_user:", ".bad_user_entry:")
exit_path=body("koronos_syscall_user_exit:", "; Called only by the dedicated IRQ0 stub")
timeout=body("koronos_user_timeout_abort:", "section .data")
assert "mov rax, cr3" in enter, "user entry must capture the actual caller CR3"
assert "mov [rel koronos_cpu_syscall_state + 48], rax" in enter
for name, text in (("syscall exit",exit_path),("timeout abort",timeout)):
    assert "mov rax, [rel koronos_cpu_syscall_state + 48]" in text, f"{name} must load saved caller CR3"
    assert "mov cr3, rax" in text, f"{name} must restore caller CR3"
    assert "koronos_bootstrap_pml4" not in text, f"{name} must not assume bootstrap CR3"
print("PASS: user return paths restore the exact saved caller CR3")
PY
