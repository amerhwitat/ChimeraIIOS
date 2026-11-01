# Koronos process-runtime port: Linux parity and safety contract

Status: engineering contract / audit baseline. This document does not claim that the process runtime is production-ready.

## Why this is a dependency set

A runnable userspace process requires all of the following to agree on one ABI:

1. Physical frame ownership and reservation.
2. Page-table/address-space ownership and user mappings.
3. ELF loading into a not-yet-active address space, with rollback on every failure.
4. Per-CPU privilege-transition state (GDT, TSS, kernel stack, syscall entry state).
5. A process object that owns its address space, kernel stack, saved register context, PID and lifecycle.
6. A scheduler/context-switch path that activates the selected address space and kernel stack.
7. Syscall entry/return and user-memory validation bound to the currently running process.

Copying only a target launcher is unsafe: it can create references to memory-management and architecture state that does not exist or is not owned by the process.

## Linux comparison

| Area | Linux x86-64 design | Koronos port requirement |
|---|---|---|
| Physical memory | Boot-time memory discovery feeds the page allocator (buddy allocator), with reserved ranges and zones | Parse the Multiboot2 map with overflow-safe bounds; reserve low memory, kernel, boot info, modules, framebuffer/MMIO and allocator metadata; do not silently truncate usable RAM |
| Address spaces | Each process has an mm_struct; VMAs describe ranges and page tables implement mappings | A process-owned address-space object, explicit mapping metadata, supervisor/user and writable/executable permissions, teardown and rollback |
| ELF loading | execve builds a new image and commits only after successful setup | Validate all ELF headers/segments first; stage mappings in a new address space; reject W+X, overlap and overflow; commit atomically |
| User entry | Architecture entry code establishes privilege transition state and a user register frame | Per-CPU TSS/RSP0 and kernel stack; validated selectors, canonical user RIP/RSP, sanitized RFLAGS; iretq/sysret path with correct frame |
| Syscalls | Entry assembly switches to trusted kernel state; kernel validates user pointers and process context | One documented ABI; preserve all required registers; validate CPL3, active PID and CR3; copy user data through checked accessors |
| Scheduling | task_struct, saved context, scheduler and address-space switching | Saved trap/context state, kernel stack per task, atomic CR3 + stack switch, interrupt-safe run queues and explicit task states |
| Exit/wait | Task exit releases resources and parent wait observes completion | Idempotent process teardown, deferred freeing when address space is active, wait/exit status and PID reuse rules |
| SMP/TLB | Per-CPU run state, locks and TLB shootdowns maintain cross-CPU correctness | Per-CPU transition stacks, allocator/address-space locks, TLB invalidation/shootdown before freeing mapped frames |

Linux is a behavioral and architectural reference, not code to copy wholesale. Koronos may begin with a deliberately smaller feature set, but must state and enforce its limits.

## Candidate implementation hazards already identified

The existing candidate branch is useful as a source reference, but is not ready to merge unchanged:

- The bitmap allocator caps physical memory at 4 GiB and assumes allocated physical frames are directly identity-mapped.
- The address-space clone assumes a particular low identity-map shape and rejects higher-half mappings; page-table table frames are accessed as physical pointers.
- The user-entry path uses global transition state rather than a fully per-CPU task entry design.
- The launcher is a synchronous bootstrap launch, not a general scheduler-backed process lifecycle.
- Mapping failure paths must prove that partially allocated page tables, mapped frames and metadata are all rolled back exactly once.
- The current process admission path is not equivalent to a transactional execve.

These constraints must be resolved or explicitly bounded by boot-time validation before enabling the runtime.

## Required implementation order

1. Frame allocator: parse and validate all Multiboot2 memory-map records; reserve every boot-owned range; support physical addresses above 4 GiB or explicitly reject boot configurations that exceed the supported ceiling; test exhaustion, fragmentation, double-free and overlap.
2. Address-space backend: use a physical-to-virtual mapping abstraction rather than assuming every frame is identity mapped; create/destroy page tables; map/unmap user pages; enforce NX/W^X; implement rollback and TLB invalidation.
3. ELF integration: validate complete ELF image and segment overlap before allocating; map PT_LOAD segments and stack; zero BSS; copy file bytes; publish the image only after every operation succeeds.
4. x86-64 entry: define selectors and frame layout from the actual GDT/IDT/TSS; install per-CPU TSS and kernel stack; validate canonical addresses and flags; preserve ABI-required registers and handle faults safely.
5. Process ownership: bind PID, address space, kernel stack and saved context in one process object; activate CR3 and kernel stack together; never free an active address space.
6. Scheduler and syscalls: add real context switching, blocking/wakeup, exit/wait and process-bound user-copy; do not report readiness for a probe-only or synchronous path.
7. Verification: host unit tests, ELF malformed-input tests, fault-injection rollback tests, assembly ABI checks, QEMU BIOS+UEFI boot, and the six target/firmware acceptance matrix.

## Release policy

Keep native init fail-closed. Do not remove native-init exit status 78 or emit readiness markers unless the target process has actually executed in CPL3, completed the required syscalls, and its target-specific postconditions have been observed. A successful compile, source-presence test, or ring-3 smoke probe alone is not production acceptance.

## Current-main integration audit (2026-11-01)

The following facts were verified directly against the ChimeraIIOS main branch during this follow-up:

- `kernel/include/chimera/process.h` defines `CHIMERA_PROCESS_LOAD_PLAN_ONLY` and the process image contains ELF segment metadata, but no owned address-space handle, kernel stack, saved register context or parent/wait state.
- `kernel/core/process.cpp` validates and records an ELF load plan and allocates a PID. It does not allocate page frames, create page tables, copy an ELF into user mappings, or enter CPL3.
- `kernel/core/syscall.cpp` explicitly rejects GETPID, EXIT and EXIT_GROUP in its compatibility dispatcher because it has no active process identity/lifecycle hook. This fail-closed behavior must not be bypassed.
- `kernel/core/interrupt.cpp` installs IDT gates with DPL0 (0x8E). Its comments explicitly defer ring-3 syscall exposure until TSS/user-stack/address-space support is installed.
- `kernel/build-koronos.sh` currently compiles this core source list: `koronos elf64 module relocate arch_init runtime runtime_loop scheduler process process_loader thread sync timer apc dpc hardware nbit firmware device multiboot_modules parallel driver learning microkernel service object utf8 platform_features compat interrupt syscall isa_registry ai_model`. It does not compile a frame allocator, address-space backend, target launcher or dedicated user-entry assembly from the proposed candidate set.
- `kernel/CMakeLists.txt` delegates the canonical Koronos build to `kernel/build-koronos.sh`; adding files to a separate test or CMake list alone would not put them in the actual ELF.

Therefore the implementation must first introduce and test the memory/architecture primitives, then wire them into this exact canonical source list and linker. It is unsafe to mark process admission as executable or change the IDT gate privilege before the corresponding per-process kernel-stack and user-memory protections are active.

## Minimum source-level exit criteria before enabling CPL3

- Remove the load-plan-only label only in the same change that introduces a real owned address-space/process object and transactional ELF loader.
- Every allocated frame has a single owner and an explicit release path; all mapping failures unwind both data and page-table frames.
- The bootstrap/kernel mappings are preserved by a documented physical-to-virtual mapping contract; no physical address is dereferenced as a pointer unless the mapping is proven.
- Each CPU has independent TSS/RSP0 and syscall transition state; a process has its own kernel stack and saved trap frame.
- CR3 changes, kernel-stack selection, active PID and syscall identity cannot disagree, including on interrupts and faults.
- User entry is exposed only after the GDT selectors, IDT privilege, TSS descriptor, canonical-address checks, NX policy and syscall return frame are validated together.
- The scheduler owns the task from first entry through exit; no synchronous launcher may free an address space while it is active.
- Fault-injection tests cover every allocation/mapping failure point and prove no leaks, double frees or stale active mappings.


## Existing candidate implementation and CI evidence (2026-11-02)

A follow-up review located the older target-launch implementation in PR #125, branch `koronos/userspace-target-launch`, head `506c76baafcc45fc08dd14fad5b1723f2d0fd24b`. Its canonical build includes `frame_allocator.cpp`, `address_space.cpp`, `process_loader.cpp`, `target_launch.cpp` and `arch/x86_64/user_entry.asm`. The associated recorded GitHub Actions runs for that commit completed successfully, including the Koronos kernel build, ELF loader unit tests, boot/ISO validation, and the Koronos userspace acceptance workflow.

Those green workflow conclusions are bounded to that candidate's checks; they do not establish the missing architectural properties below. The candidate allocator uses a fixed 4-GiB physical limit and direct physical-address dereferences. The address-space backend also treats physical frame addresses as kernel pointers and clones only a specific low identity-map shape. User-entry assembly holds a single global TSS, syscall stack and transition state. The target launcher is a synchronous bootstrap call; its YIELD syscall is a no-op until scheduler-owned address-space switching exists. The process record remains marked `CHIMERA_PROCESS_LOAD_PLAN_ONLY`.

Consequently, passing build and probe workflows must not be conflated with the requested upgrades: a >4-GiB-safe allocator, a real physical-to-virtual mapping abstraction, per-CPU privilege-transition state, scheduler-owned independent tasks, wait/exit semantics, or AP/SMP safety. The implementation port remains gated on those properties and corresponding fault-injection and QEMU tests.
