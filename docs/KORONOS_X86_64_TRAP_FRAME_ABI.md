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
RFLAGS bit 1 and IF, and rejects TF, IOPL, DF, NT, AC, and VM. The ISR executes CLD before entering C so a user-supplied direction flag cannot violate the kernel's SysV C ABI; IRETQ restores the saved user flags. The policy is deliberately
conservative; LA57 user addresses are not accepted by this ABI.

Host tests cover the exact structure offsets and invalid selectors, addresses,
and privileged RFLAGS states.

## Deliberately not enabled

This change does **not** enable the syscall IDT gate at DPL3, execute IRETQ into
a user process, switch CR3, identify the current process from trusted per-CPU
state, dispatch process-bound syscalls, or implement process exit/reaping.
The per-CPU TSS stack setter now rejects updates while IF is set, preventing
maskable interrupts from observing a stack transition. It still relies on the
caller to target the owning CPU; APIC current-CPU binding is not implemented.
The existing DPL0 IDT policy and native-init exit-78/DAPS release gates remain
unchanged. A later integration must bind the frame to the current process,
activate that process's kernel stack in the owning CPU's TSS with interrupts
disabled, validate address-space mappings, and implement scheduler-owned
deferred teardown before CPL3 is enabled.

## Per-CPU ownership and kernel-stack mapping checks

The CPU initializer now records the executing CPU's APIC identity, rejects a
duplicate APIC identity among registered logical CPUs, installs a CPU-local
GS base pointing at that CPU's state, and verifies the logical CPU ID through
GS before marking the CPU ready. The current-CPU APIs cross-check the GS
logical ID against the APIC identity. TSS stack updates reject remote-CPU
requests and require IF=0. AP startup and registration for secondary CPUs are
still not implemented; the current boot path initializes the BSP only.

Address-space validation now includes a supervisor-kernel-range check. Process
ELF loading verifies that the newly allocated kernel stack is present,
supervisor-only at the leaf mapping, and writable in the process address space
before retaining the loaded process. This verifies the existing four-GiB
supervisor identity-map contract; it does not yet provide a shared higher-half
kernel mapping or activate a process CR3/TSS pair.

## CR3 transition guard

Address-space activation and restoration now require a verified current-CPU
GS/APIC identity. The transition preserves the prior RFLAGS, masks interrupts
for the CR3 write, places compiler/memory barriers around the root switch, and
restores the caller's interrupt state. The address-space self-test exercises
the switch and restore on the initialized BSP. The current supervisor mapping
contract remains the verified four-GiB identity map cloned into each process
root; shared higher-half kernel page-table subtrees and AP startup are still
future work.
