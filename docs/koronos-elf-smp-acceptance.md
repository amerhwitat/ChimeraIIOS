# Koronos ELF userspace and SMP acceptance contract

This is the release gate for the production x86-64 Koronos path. A successful compile, GRUB menu, or kernel scheduler loop is not evidence of userspace execution or SMP progress.

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

ELF tests cover truncated headers/tables, out-of-file segment ranges, integer overflow, invalid alignment, overlapping segments, unsupported type/machine, invalid entry, W+X, allocation/mapping failure, BSS zeroing, stack construction, and rollback without leaked mappings.

Scheduler tests cover concurrent enqueue/dequeue, wake-vs-block races, exit while another CPU attempts wake, migration, repeated yield, no double-run, and idle behavior. Use a race-capable hosted model where possible, plus QEMU SMP integration.

## Evidence policy

QEMU acceptance requires serial output containing:
- ELF_USERSPACE: entry reached — emitted by the actual ring-3 test program;
- SMP: cpu online id=N for at least two distinct nonzero CPUs;
- SCHED: task progress cpu=N from actual scheduled tasks on at least two distinct CPU IDs;
- ELF_TEST: bss=zero stack=valid permissions=valid — emitted after runtime checks.

Timeout, reset, triple fault, a marker emitted only before user entry, or an ISO that merely reaches the boot menu is a failure. Keep the gate explicit until production implementation and evidence pass.
