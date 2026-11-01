# Koronos runtime implementation status

Date: 2026-11-01

This is an implementation ledger, not a production-readiness declaration.

## 1. Physical frame ownership — implemented with an explicit ceiling

- Multiboot2 usable and non-usable ranges are processed with overflow checks.
- Reserved pages are tracked independently so later usable ranges cannot re-admit them.
- Allocated/free ownership is tracked per page; contiguous free validates the entire range before changing any bit.
- The supported physical range is explicitly limited to addresses below 4 GiB. A usable range above that limit is rejected, not silently clipped.
- Host tests cover reservations, contiguous allocation, double-free, alignment, above-ceiling usable RAM, overflow and mapper callback bounds.
- Chimera's bootstrap page tables now map the full low 4-GiB physical range (four 1-GiB PDPT entries); the exported bootstrap PML4 symbol is used by the address-space backend.

## 2. Address-space backend — implemented and boot-self-tested; mapping ceiling remains

- Both implementation branches now compile the address-space backend.
- Page-table and user-frame aliases use `koronos_frame_phys_to_virt`; the default mapper remains the low-4-GiB identity map.
- The backend clones the current bootstrap kernel identity map, creates user mappings above 4 GiB, enforces user/supervisor and W^X/NX permissions, and tracks page-table/data frames for teardown.
- Teardown refuses to reclaim an address space while its CR3 is active on the current CPU.
- ChimeraIIOS QEMU boot-matrix CI passed on commit `19a824ab`; its trace explicitly records the frame allocator initialization and the address-space self-test passing, including frame reclamation.
- This is still a single-CPU backend. It does not implement a higher-half/direct-map architecture or SMP TLB shootdowns. The default physical mapper is still the identity mapping.

## 3. Transactional ELF loading — partial, with fault-injected rollback test

- The loader validates the ELF and segment plan before creating mappings.
- It destroys the partially built address space when a segment or stack mapping fails and publishes the output structure only after success.
- Host tests inject a failure while mapping the stack after the PT_LOAD mapping and assert teardown plus unchanged caller output.
- The canonical Koronos build runs the allocator, ELF-loader rollback and process-admission unit runners.
- Exhaustive allocation-failure injection, physical-mapper fault injection and runtime proof are still outstanding.

## 4. Per-CPU GDT/TSS/syscall state — not implemented

The Octavian candidate still uses a global TSS/syscall-stack/transition state for the bootstrap CPU. The current kernel starts only CPU0. This is not per-CPU task-entry state; do not enable AP process execution on this design.

## 5. Process-owned address-space metadata — partially implemented

- The process record now stores the address-space handle, CR3 root, user entry and user stack after the transactional loader succeeds.
- The target launcher in OctavianOS binds and clears this ownership record around execution and teardown.
- ChimeraIIOS has the same process ABI and bind/clear operations, but does not yet have the complete target launcher integrated.
- Kernel-stack base/top, saved RSP/RIP, parent PID and exit status fields are reserved but remain zero/unimplemented. There is no scheduler-owned task context yet.

## 6. Scheduler lifecycle — not implemented

The current scheduler runs cooperative callbacks. It does not switch task register contexts, kernel stacks and CR3 as one atomic task transition. The parallel scheduler entry remains unavailable; serial callback dispatch is not SMP evidence. There is no general process wait/parent/reap lifecycle.

## 7. Cross-repository parity — partial and measured

The allocator implementation/header/tests, address-space implementation/header, ELF64 validation implementation/header, process implementation/header, process-admission test and process-loader rollback test are being synchronized. The target launcher and user-entry assembly remain Octavian-specific and are not treated as a verified shared runtime.

## 8. Verification status

- ChimeraIIOS QEMU x86-64 boot matrix: passed on commit `19a824ab`; the run built Koronos, built desktop artifacts, created the Multiboot2 test ISO, booted it in QEMU, and observed the kernel readiness marker.
- The same trace shows the allocator and address-space self-tests passing.
- The ELF-loader rollback test passed in that build.
- The process-admission/scheduler regression workflow passed on the same branch revision.
- Latest OctavianOS kernel build and six-case acceptance for the newer process-ownership/ELF synchronization commits are still pending CI.

A successful kernel boot or self-test is not full userspace production acceptance. Real CPL3 process execution, process-bound syscalls, filesystem OPEN/READ/CLOSE, writable `/tmp`, installer persistence, recovery postconditions and SMP overlap evidence remain required.

## Release boundary

Keep native-init fail-closed behavior and exit status 78 until all process-memory, entry, syscall, scheduler and target postconditions are verified. Do not mark either OS production-ready based on source presence, host tests or an address-space self-test alone.
