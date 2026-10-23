# Linux-to-Koronos Porting Map and Bootability Plan

**Status:** engineering plan and acceptance contract; not a claim of a bootable production kernel.

## Summary

Use Linux as an architectural reference and import source only for small, independently reviewable components whose dependencies, architecture, and license are understood. Do not transplant Linux's mm_struct, task_struct, scheduler, VFS, syscall entry, or driver files into Koronos as isolated files: these are coupled to Linux internal APIs, Kconfig, architecture headers, locking, memory allocators, and lifecycle rules.

The project remains fail-closed until actual production ISO traces establish target readiness. A successful build or source-contract test is not a successful boot.

## Linux concept → Koronos equivalent → closure work

| Linux concept | Role in Linux | Koronos closure work |
|---|---|---|
| x86 boot protocol, start_kernel() | Normalize boot state and initialize core subsystems | Audit Multiboot2 handoff, memory map, early console, boot modules, and ordered init; test BIOS and UEFI separately |
| Physical page allocator (memblock then buddy allocator) | Reserve boot memory and allocate physical pages | Verify reserved ranges, allocator invariants, exhaustion handling, and page ownership before process address spaces |
| mm_struct / VMAs / page tables | Own process virtual memory and map ELF segments | Koronos needs per-process address-space ownership, PT_LOAD permissions, BSS, user stack, user-pointer validation, and safe teardown |
| load_elf_binary() / binfmt_elf | Validate and map ELF executable segments | Reuse the validation design, not Linux-internal code: overflow-safe range checks, PT_LOAD alignment, segment overlap policy, NX/W^X, entry-point validation, rollback on failure |
| entry_SYSCALL_64 / IDT interrupt entry | Establish privilege boundary, save context, dispatch syscalls, return safely | Koronos must choose one documented native ABI, verify saved CPL/CR3/current PID, validate every user pointer, and test return/exit paths. Do not mix SYSCALL and INT 0x80 acknowledgement semantics |
| task_struct / scheduler / wait queues | Process/thread identity, runnable state, blocking, wakeup, exit, reaping | Define process lifecycle APIs before implementing spawn/exec/wait/exit/reap. Never report a service healthy from a declaration alone |
| Linux VFS (file, inode, dentry, mount namespace) | Per-process descriptors and filesystem namespace | Connect Koronos's validated RAMFS extraction to atomic root publication, per-process descriptor ownership, path confinement, and bounded user-buffer copying |
| rootfs / initramfs unpack | Establish initial root filesystem and handoff to init | Ensure unpack is bounded, transactional, duplicate/prefix/symlink safe, and visible to ring-3 processes before launching init |
| PID 1 / init and service supervision | Start and supervise userspace services | Implement a Koronos supervisor that spawns real service processes, checks exit status/health, restarts or fails closed, and emits readiness only after target-specific health checks |
| Block layer / filesystem sync | Durable writes to storage | Installer needs a real block-device/filesystem path, flush/sync semantics, installation transaction, cold reboot, and independent readback |
| AP startup / per-CPU scheduler | Bring up secondary CPUs and run work concurrently | Demonstrate AP online acknowledgements, per-CPU stacks/state, synchronized shared data, and overlapping execution on distinct AP/BSP CPU IDs |
| framebuffer/DRM and input drivers | Display and interact with desktop | First establish framebuffer mode and input/device health; then validate Aurora session/compositor, not just a wallpaper or boot menu |

## Source-import rules

1. Prefer an implementation derived from documented algorithms and Koronos-owned interfaces over copying a Linux internal source file.
2. If code is copied from Linux, retain its copyright/license headers and provenance, comply with GPL-2.0-only or GPL-2.0-or-later terms as applicable, and have repository licensing reviewed before merge.
3. Never import code with hidden assumptions about Linux locks, RCU, per-CPU APIs, slab allocators, struct page, struct file, or task_struct without porting the full dependency contract.
4. Keep architecture-specific x86-64 entry code separate from portable process/VFS/service logic.
5. Every imported component must include a standalone test, integration test, failure-path test, and a documented ownership/locking contract.

## Current root causes confirmed in the source audit

- Native init intentionally exits with status 78 after its VFS self-test because operational target services are unavailable. Do not remove this guard to make the log look green.
- Installer launch explicitly rejects a missing storage-backed root namespace. Staging an installation.img module is not equivalent to mounting a writable installed filesystem or proving persistence.
- The syscall surface has VFS calls and a process identity query, but no completed process-spawn/exec plus wait/reap lifecycle wired into the native syscall path. Service metadata/dependency bookkeeping does not launch or supervise processes.
- The closeout checker had accepted legacy USERSPACE READY probe markers as if they proved a production service healthy. It now requires the target-specific USERSPACE TARGET READY component marker with the same nonzero PID as the user-originated syscall.
- The OctavianOS vendored closeout checker did not inspect raw trace semantics in the same way as Chimera's checker. Its gate and regression tests have now been synchronized to the stricter implementation.

## Required implementation order

### Phase A — boot and memory safety
- Verify Multiboot2 module bounds, memory map reservations, physical allocator integrity, and page-table ownership.
- Test malformed ELF, overflow, segment overlap, BSS zero-fill, NX/W^X, stack guard/range, and loader rollback.
- Boot the actual ISO under BIOS and UEFI with serial/debugcon traces.

### Phase B — process and syscall lifecycle
- Specify a single stable native syscall ABI and document register arguments, return/error convention, pointer validation, and privilege-entry semantics.
- Implement process-owned descriptors and root namespace; add process creation/exec, wait, exit, reap, and scheduler state transitions.
- Test invalid pointers, inaccessible pages, bad descriptors, double exit, child crash, and process cleanup.
- Keep USERSPACE TARGET READY unavailable until the target service is actually healthy.

### Phase C — target services
- Live: start required device/display services and Aurora session; prove frame output and health.
- Installer: detect/validate storage, mount a real writable target filesystem, install transactionally, flush, cold reboot, and read back independently.
- Recovery: run a real repair operation on disposable test storage and verify postconditions.

### Phase D — firmware, SMP, and evidence
- Run the actual production ISO for Live/Installer/Recovery under BIOS and UEFI: six separate cases.
- Verify ring-3 rootfs OPEN/READ/CLOSE and Live/Recovery tmpfs CREATE/WRITE/READ/TRUNCATE from raw traces.
- Demonstrate AP startup and overlapping execution on two or more distinct CPUs.
- Generate the evidence bundle only from raw harness outputs; bind artifact hashes; run DAPS; inspect failed job logs; repeat until all tests pass.

## Acceptance rule

PASS requires all six production cases, target-specific service health, matching nonzero kernel-owned syscall/readiness PID, process-visible filesystem operations, display/Aurora evidence, installer cold-reboot persistence, recovery postconditions, and AP-backed concurrent SMP. Candidate smoke results and JSON booleans without artifact-backed trace validation do not satisfy production acceptance.
