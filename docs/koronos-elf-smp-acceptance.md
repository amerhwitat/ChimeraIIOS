# Koronos ELF userspace and SMP acceptance contract

This is the release gate for the production x86-64 Koronos path. A successful compile, GRUB menu, or kernel scheduler loop is not evidence of userspace execution or SMP progress.

## Current implementation boundary

The changes harden ELF admission and add a transactional ELF loading engine in `kernel/core/elf_loader.cpp`. The engine allocates zeroed pages through a supplied backend, copies PT_LOAD bytes, leaves BSS zeroed, installs user mappings with requested permissions, creates a 64-KiB stack with an unmapped guard page, and rolls back pages/mappings if loading or handoff fails. The architecture backend is not implemented: the current tree does not provide a real physical-page allocator, user PTE/NX manager, TSS/user GDT setup, or audited ring-3 return path. Therefore this loader is not wired into boot and does not prove actual userspace execution. The current runtime loop dispatches CPU 0 only; AP startup and assembly context switching remain blockers.

| Acceptance item | Current status |
|---|---|
| ELF header/table and segment admission checks | Partially implemented; host regression tests added |
| Transactional ELF loader engine | Implemented against callbacks; requires a real architecture backend and QEMU validation |
| Real user PTE mapping, NX/W^X, physical allocation | Not implemented in production backend |
| Guarded 64-KiB stack construction | Loader engine implemented; not boot-integrated |
| Audited ring-3 return frame and TSS | Not implemented |
| Discover/start APs and initialize per-CPU stacks/state | Not implemented |
| Assembly context switch and address-space/TLS/FPU state | Not implemented |
| SMP-safe run queues and task ownership | Partial cooperative model only; no production SMP execution |
| Host regression tests | Admission/scheduler suite updated to compile loader; CI not yet verified |
| Full ISO build and QEMU SMP/userspace evidence | Not run; required before release verification |

## ELF load/handoff requirements

Accept only ELF64 little-endian x86-64 ET_EXEC images supported by the current ABI. Before changing address-space state, validate ELF/program-header bounds, PT_LOAD file/memory sizes, arithmetic overflow, alignment, user virtual-address range, and segment overlap policy. Reject unsupported interpreters, dynamic relocations, malformed headers, W+X segments, and entry points outside executable load segments unless explicitly supported by the ABI.

For each accepted PT_LOAD, the new loader engine allocates zeroed pages via `chimera_elf_loader_ops`, copies exactly `p_filesz` bytes using the validated file offset and page offset, thereby preserving zero-filled BSS, then asks the backend to install user mappings with the derived permissions. It rolls back already installed mappings and allocated frames if any later operation fails. The backend must implement actual physical allocation, supervisor writable aliases, user PTEs, NX, TLB invalidation, and atomic map-failure semantics; these are not yet present in the production x86-64 path. The `enter_user` callback must perform a real audited privilege transition and must not return on success; a returning callback is treated as failure and triggers rollback.

Construct a guarded user stack, define initial register/ABI state, install address-space and privilege-transition state, and enter via one audited architecture-specific return-to-user path. On x86-64, document the iretq/sysretq selector and flags contract. Never call an ELF entry point as a kernel function or merely change RIP.

## SMP and scheduler invariants

- BSP discovers enabled APIC processors and starts APs through a bounded INIT/SIPI state machine; timeout or malformed firmware data must leave the BSP usable.
- Each CPU has isolated bootstrap/interrupt stacks, per-CPU scheduler state, current-task pointer, and interrupt bookkeeping before being marked online.
- Context switch saves/restores ABI-required callee-saved state, stack pointer, address-space root, TLS/per-CPU state, and FPU/SIMD ownership state according to the architecture contract.
- Run-queue operations and task-state transitions are synchronized. A task can be queued or running on only one CPU at a time. Yield/block/exit/wake act on an explicit task/current-CPU context, not a shared global current task.
- Never hold a scheduler lock across address-space switching or user entry unless the locking protocol explicitly guarantees safe release.
- CPU-online and task-progress counters must be emitted by actual AP/task paths, never synthesized by the test harness.

## Negative tests

The hosted tests currently cover valid ELF load-plan admission, truncated program-header tables, W+X rejection, invalid entry rejection, blocked-task wake, and nested-dispatch ownership. This is an initial regression subset, not complete conformance.

The required suite must additionally cover out-of-file segment ranges, integer overflow, invalid alignment, overlapping segments, unsupported type/machine, allocation/mapping failure, BSS zeroing, stack construction, rollback without leaked mappings, concurrent enqueue/dequeue, wake-vs-block races, exit-vs-wake, migration, repeated yield, and idle behavior. Use a race-capable hosted model where possible, plus QEMU SMP integration.

## Evidence policy

QEMU acceptance requires serial output containing:
- ELF_USERSPACE: entry reached — emitted by the actual ring-3 test program;
- SMP: cpu online id=N for at least two distinct nonzero CPUs;
- SCHED: task progress cpu=N from actual scheduled tasks on at least two distinct CPU IDs;
- ELF_TEST: bss=zero stack=valid permissions=valid — emitted after runtime checks.

The fail-closed script is tests/koronos/elf_smp_qemu_acceptance.sh. It must be run against the newly rebuilt ISO; its markers must originate from the real kernel and userspace test, not from the test harness.

Timeout, reset, triple fault, a marker emitted only before user entry, or an ISO that merely reaches the boot menu is a failure. Keep the gate explicit until production implementation and evidence pass.
