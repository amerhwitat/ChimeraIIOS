# Koronos ELF userspace and SMP acceptance contract

This is the release gate for the production x86-64 Koronos path. A successful compile, GRUB menu, or kernel scheduler loop is not evidence of userspace execution or SMP progress.

## Current implementation boundary

The changes in this branch harden ELF *admission* validation and make the cooperative scheduler's state-transition API CPU-specific. They do not yet implement physical page mapping, BSS clearing in mapped memory, ring-3 entry, AP startup, per-CPU stacks, or machine context switching. The current runtime loop dispatches CPU 0 only. These are explicit blockers, not features inferred from a load-plan or a successful compile.

| Acceptance item | Current status |
|---|---|
| ELF header/table and segment admission checks | Partially implemented; host regression tests added |
| Map pages, copy segments, zero BSS, enforce PTE permissions | Not implemented |
| Construct user stack and audited ring-3 return frame | Not implemented |
| Discover/start APs and initialize per-CPU stacks/state | Not implemented |
| Assembly context switch and address-space/TLS/FPU state | Not implemented |
| SMP-safe run queues and task ownership | Partial cooperative model only; no production SMP execution |
| Host regression tests | Added; must pass CI before merge |
| Full ISO build and QEMU SMP/userspace evidence | Not run; required before release verification |

## ELF load/handoff requirements

Accept only ELF64 little-endian x86-64 ET_EXEC images supported by the current ABI. Before changing address-space state, validate ELF/program-header bounds, PT_LOAD file/memory sizes, arithmetic overflow, alignment, user virtual-address range, and segment overlap policy. Reject unsupported interpreters, dynamic relocations, malformed headers, W+X segments, and entry points outside executable load segments unless explicitly supported by the ABI.

For each accepted PT_LOAD:
- allocate/map user pages for the full memory range;
- copy exactly p_filesz bytes from the validated file range;
- zero [p_vaddr + p_filesz, p_vaddr + p_memsz) for BSS;
- derive PTE permissions from PF_R/PF_W/PF_X and enforce NX/W^X;
- roll back mappings and references if any operation fails.

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
