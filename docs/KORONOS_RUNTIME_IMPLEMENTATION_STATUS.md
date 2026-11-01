# Koronos runtime implementation status

Date: 2026-11-01

This is an implementation ledger, not a production-readiness declaration.

## Current tranche

### 1. Physical frame ownership — implemented with an explicit ceiling

- Multiboot2 usable and non-usable ranges are processed with overflow checks.
- Reserved pages are tracked independently so later usable ranges cannot re-admit them.
- Allocated/free ownership is tracked per page; contiguous free validates the entire range before changing any bit.
- The supported physical range is explicitly limited to addresses below 4 GiB. A usable range above that limit is rejected; it is not silently clipped.
- Host tests cover reservations, contiguous allocation, double-free, alignment, above-ceiling usable RAM and overflow.

### 2. Physical-to-virtual mapping — API added; backend remains constrained

- `koronos_frame_set_mapper` and `koronos_frame_phys_to_virt` define a replaceable physical-frame mapping interface.
- The default mapper is the existing low-4-GiB identity map.
- OctavianOS's candidate address-space backend now uses this interface for page-table and user-frame aliases and refuses to reclaim a CR3 that is active on the current CPU.
- This is not yet a higher-half/direct-map implementation and does not provide SMP TLB shootdowns.
- ChimeraIIOS currently has the allocator and mapping API; its production address-space backend still needs implementation and integration.

### 3. Transactional ELF loading — partial

- The loader validates the ELF and segment plan before creating mappings.
- It destroys the partially built address space when a segment or stack mapping fails and publishes the output structure only after success.
- Host tests now inject a failure while mapping the stack after the PT_LOAD mapping and assert teardown plus unchanged caller output.
- Exhaustive allocation-failure injection, physical mapper fault injection and runtime proof are still outstanding.

### 4. Per-CPU GDT/TSS/syscall state — not implemented

The current Octavian candidate uses global TSS/syscall-stack/transition state. It is a single-bootstrap-CPU path, not per-CPU task-entry state. Do not enable AP process execution on this design.

### 5. Process-owned stacks, saved contexts, CR3 and PID — not implemented as a general task model

The launcher records a PID and active root in bootstrap-global state. The process metadata is not yet a scheduler-owned task object containing an independently owned kernel stack, saved context, address space, parent/wait state and exit status.

### 6. Scheduler lifecycle — not implemented

The current scheduler runs cooperative callbacks. It does not switch task register contexts, kernel stacks and CR3 as one atomic task transition. The parallel scheduler entry remains unavailable; serial callback dispatch is not SMP evidence.

### 7. Cross-repository parity — partial

The allocator implementation, allocator header, allocator unit test and ELF-loader unit test are byte-identical between the current ChimeraIIOS and OctavianOS implementation branches. The full Koronos source trees intentionally remain divergent until the architecture, process and scheduler components are reviewed and reconciled.

### 8. Verification — in progress

The allocator and ELF rollback tests are wired into the canonical Koronos build. CI compiler/linker and QEMU workflows are running on the implementation branches. A successful compile or six-case smoke run does not replace the full release gate: real CPL3 process evidence, filesystem syscalls, writable `/tmp`, installer persistence, recovery postconditions and SMP overlap evidence are still required.

## Release boundary

Keep native-init fail-closed behavior and exit status 78 until all process-memory, entry, syscall, scheduler and target postconditions are verified. Do not mark the OS production-ready based on source presence, host tests or a bootstrap ring-3 probe alone.
