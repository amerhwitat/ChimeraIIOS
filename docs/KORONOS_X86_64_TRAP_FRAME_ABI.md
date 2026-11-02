# Koronos x86-64 normalized interrupt and user trap-frame ABI

Status: **frame-layout foundation implemented; CPL3 remains disabled**.

## Stack contract

Every ISR stub now presents the same prefix to C:

| Offset from frame pointer | Field |
| ---: | --- |
| 0–112 | GPRs: r15, r14, r13, r12, r11, r10, r9, r8, rdi, rsi, rbp, rbx, rdx, rcx, rax |
| 120 | vector |
| 128 | error code (CPU supplied or stub-synthesized zero) |
| 136 | RIP |
| 144 | CS |
| 152 | RFLAGS |
| 160 | old RSP (only on privilege transition) |
| 168 | old SS (only on privilege transition) |

The ISR always removes the normalized vector and error-code slots before IRETQ.
The C dispatcher call stack is aligned to the x86-64 SysV ABI independently of
the interrupted stack alignment. The original frame remains addressable through
the second dispatcher argument.

## User-return validation

`chimera_x86_64_trap_frame_is_user()` is a pure validation helper. It requires
the configured ring-3 code/data selectors, nonzero 48-bit canonical RIP/RSP,
RFLAGS bit 1 and IF, and rejects IOPL, NT, and VM. The policy is deliberately
conservative; LA57 user addresses are not accepted by this ABI.

Host tests cover the exact structure offsets and invalid selectors, addresses,
and privileged RFLAGS states.

## Deliberately not enabled

This change does **not** enable the syscall IDT gate at DPL3, execute IRETQ into
a user process, switch CR3, identify the current process from trusted per-CPU
state, dispatch process-bound syscalls, or implement process exit/reaping.
The existing DPL0 IDT policy and native-init exit-78/DAPS release gates remain
unchanged. A later integration must bind the frame to the current process,
activate that process's kernel stack in the owning CPU's TSS with interrupts
disabled, validate address-space mappings, and implement scheduler-owned
deferred teardown before CPL3 is enabled.
