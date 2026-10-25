# Koronos task context-switch and syscall-boundary implementation plan

Status: design contract only; context switching is not implemented and production release remains blocked.

## 1. Keep the three frames distinct

- `koronos_user_syscall_frame` is the saved GPR frame built by `user_entry.asm` at native SYSCALL entry. Its 15 qwords are laid out in reverse push order. RCX contains the user return RIP and R11 contains user RFLAGS.
- `koronos_x86_64_switch_context` is the cooperative kernel continuation ABI. It is not a syscall frame and does not contain all interrupt-return state.
- A full interrupt/trap frame is needed for preempting arbitrary user/kernel execution. It must encode the vector/error code and privilege-transition stack consistently with the common interrupt stubs.

The current assembly enters userspace synchronously and resumes one saved kernel caller on exit, timeout, or user page-fault abort. Do not wire a context switch into that path by reusing the bootstrap globals.

## 2. Proposed x86-64 switch ABI

The existing 104-byte context layout is:
- offsets 0..40: R15, R14, R13, R12, RBX, RBP
- offset 48: RSP
- offset 56: RIP
- offset 64: RFLAGS
- offset 72: CR3 root physical address
- offset 80: FS base
- offset 88: user GS base
- offset 96: pointer to owned, 16-byte-aligned FXSAVE/XSAVE state

The assembly entry should accept pointers to outgoing and incoming contexts. It must save the outgoing callee-saved GPRs, RSP, and a resume RIP; then switch to a validated incoming kernel stack and address space, restore per-task TLS and FP state, restore the intended flags under an interrupt policy, and transfer to the incoming RIP. A first-run context must point at a dedicated trampoline that establishes ABI stack alignment and calls a typed task-entry function; it must not return. The scheduler must hold a valid reference to both contexts throughout the switch.

Before implementing assembly, decide and encode:
1. Whether CR3 stores a physical root or CR3 value including PCID; never mix the two.
2. Whether kernel mappings are shared across roots and which TLB invalidation protocol applies.
3. Where kernel GS/per-CPU state lives; user GS must not be restored as kernel GS.
4. How FS/GS bases are switched safely (MSRs or FSGSBASE after feature checks).
5. FXSAVE versus XSAVE policy, CPUID/XCR0 feature negotiation, alignment, and per-task ownership.
6. Interrupt disable/restore points and lock handoff; never switch while holding a lock that the incoming task must acquire.
7. How preemption saves a full trap frame, unlike cooperative ABI-call switching.
8. How task exit switches to a reaper context before freeing the exiting task's stack/address space.

## 3. Syscall user-memory boundary review

Current `target_launch.cpp` helpers reject null/overflow/non-user ranges, verify active CR3 against the active address-space object, pin pages, validate the full mapping and permissions, copy byte-wise, and unpin. The VM range validator checks every page's metadata generation, resident state, physical-page/PTE agreement, U/S and write permissions through the page-table walk.

The native `read` path now validates the complete writable destination after pinning and before calling VFS read. This ordering matters: an invalid user buffer must not consume bytes or advance the file descriptor offset before copy-out fails. It still needs CI/runtime testing, including unaligned spans, cross-page spans, read-only pages, unmapped second pages, overflow, stale roots, pin/unpin failures, and concurrent unmap attempts.

Rules for every future syscall:
- Validate arithmetic and policy before dereferencing any user pointer.
- Pin the full range before I/O or other irreversible side effects.
- Validate the entire range against the calling task's root and required permissions.
- Copy through a fault-contained user-copy primitive; a validation pass alone does not eliminate mapping races.
- Unpin on every exit path; never use user memory as a kernel format string or retain raw user pointers after syscall return.
- Bound lengths and copy strings into kernel-owned buffers with a mandatory terminator.
- If copy-out can fail after a side effect, define transactional/offset semantics explicitly.

## 4. Required verification before integration

- Compile-time ABI assertions for sizes and offsets, including architecture/compiler configurations.
- Assembly disassembly checks and a small context round-trip test that proves every callee-saved register and stack alignment survives a switch.
- First-run trampoline test; switch A→B→A; distinct CR3 roots; TLS and FP/SIMD isolation; terminal task stack reclamation only from another stack.
- User-memory tests for zero length, null, lower-bound, canonical limit, arithmetic overflow, cross-page, missing mapping, supervisor-only parent entry, read-only destination, stale root, and pin accounting.
- A real ring-3 read test proving invalid destinations do not change the VFS offset, followed by a valid read of the same bytes.
- Production closeout remains gated on all six target/firmware traces, Aurora/Marine readiness handshakes, installer persistence, recovery postconditions, and two-CPU overlapping execution.

No generic probe marker, compile-only test, or source-level assertion substitutes for runtime acceptance.
