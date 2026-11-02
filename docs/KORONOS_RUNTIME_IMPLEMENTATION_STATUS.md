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

- The Octavian boot path now explicitly initializes one online scheduler CPU and one learning worker, matching Chimera's fail-closed BSP-only initialization. Hardware-reported logical CPU count is diagnostic only until AP startup and per-CPU transition state exist. This prevents the kernel from advertising offline APs as runnable scheduler CPUs; it is not SMP implementation.
- Octavian's `chimera_sched_run_parallel()` now returns 0 unconditionally, matching Chimera, until AP startup, per-CPU execution contexts and reschedule IPIs exist. The prior Octavian implementation iterated callbacks serially with synthetic CPU indices, which was not simultaneous multicore execution. The existing scheduler regression asserts that a submitted callback is not run by this API; serial range dispatch remains explicitly separate.
  The regression host runner is now invoked by `kernel/build-koronos.sh` in both repositories so it executes before each freestanding kernel build (Octavian commits `aeb1a7a8d1d9edb501de5dd21f0ecb1de7b07400`, `2ddafd5adbffea614497ae81384b46ca2801dae7`; Chimera commits `3264f74da93b2788a3ff43ee7564bc7faed4aa75`, `f66c0a130f0ec7c517a7788b96c249b0293a9172`).

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

## 9. Native full-ISO init handoff audit — blocked by missing production payload

An audit of the actual full-ISO GRUB menu and native build workflow explains why the full-ISO Live/Installer/Recovery handoff verifier cannot pass on the current production ISO:

- The full-ISO GRUB Live entries load only `chimera-live-initramfs.img` and `live-manifest.json`; they do not load a `chimera-user-init-elf` module.
- The Installer entry loads the installation image, manifest, contract, phases and profiles only; it does not load a native init ELF.
- The Recovery entry loads the recovery initramfs and manifest only; it does not load a native init ELF.
- The native kernel launcher searches exclusively for exactly one `CHIMERA_MODULE_USER_INIT_ELF`. If none is present it returns without launching a process. The target tasks explicitly log that Live/Installer/Recovery handoff is withheld.
- The only `user_init_smoke.c` source found in the Octavian branch is under kernel tests. It is an acceptance probe, not a production init, and must not be inserted into a release ISO as a substitute for a real init/service manager.
- The workflow's three verifier inputs are therefore not equivalent to three production user-mode boot traces. The isolated userspace-acceptance workflow builds separate probe ISOs; its results cannot establish full-ISO production handoff.

This is a real release blocker, not a missing log line. Keep the verifier fail-closed and publication skipped. To resolve it, implement target-specific production native init ELFs and the service/supervision/filesystem/syscall paths they require; wire those exact binaries into each GRUB target entry and final ISO; then rerun the six BIOS/UEFI cases and verify actual process PID, CPL3 syscall, VFS OPEN/READ/CLOSE, writable /tmp, target-specific installer/recovery postconditions and Aurora health. Do not make the verifier pass by adding the test probe, synthesizing markers, or weakening the gate.

## 11. BSP-only scheduler safety parity

Octavian's boot path previously passed the hardware-reported logical CPU count directly to the cooperative scheduler even though no AP startup path exists. This was inconsistent with Chimera and could expose offline CPU slots to scheduler callers. Commit `5c7ff4f54734b22e92226c94020b21562ac4ea42` changes Octavian to initialize the scheduler and learning runtime with one online CPU (the BSP), while logging the detected logical CPU count separately. AP startup, per-CPU GDT/TSS/syscall state, IPIs, and simultaneous execution remain unimplemented; this is a safety correction, not SMP support.

## 10. Latest compiler portability validation

- Chimera's latest Windows build step passed after the MSVC interlocked and freestanding byte-copy/zero changes; its Windows test step was still running at the last status poll.
- Chimera Linux build/tests passed in the same CI/CD run.
- This does not validate the missing production init payload or any scheduler/SMP feature.

## 12. Runtime implementation dependency audit and current work queue (2026-11-02)

This section records the exact blockers found in the shared Koronos source. It is a dependency/acceptance ledger, not a claim that these features have been implemented.

### 12.1 Native target-init prerequisites

- kernel/core/interrupt.cpp installs all IDT gates as DPL0 and explicitly withholds ring-3 software syscall entry until a TSS/user stack and validated user address space exist.
- kernel/core/syscall.cpp is a compatibility-ABI translator, not the process-bound native syscall implementation. GETPID and EXIT deliberately return ENOSYS without caller identity/lifecycle hooks; OPEN/READ/WRITE/SEEK/CLOSE filesystem operations are not dispatched here.
- kernel/core/process.cpp admits and records an ELF load plan only. It does not create an executing task, load a saved register context, install a per-process kernel stack or enter CPL3.
- kernel/core/koronos.cpp explicitly reports that initramfs registration is not a user handoff. Live/Installer/Recovery tasks currently block after reporting that no executable ring-3 path is connected.
- kernel/core/service.cpp declares core service identities; its own bootstrap comment says it does not start them. There is no verified block-device backend + mounted persistent VFS + initramfs VFS + file descriptor/syscall layer sufficient for a real init supervisor.
- The current source tree contains no production target init ELF build source or artifact. The user_init_smoke.c probe exists only in tests and is not a production service manager.

Therefore, creating three ELF files or wiring GRUB module names alone would be unsafe and misleading: they would not have a working ring-3 transition, file/syscall services, process lifecycle or service supervision. Keep all target handoffs fail-closed until the dependencies below are implemented.

### 12.2 Required dependency order

1. Per-CPU descriptor/TSS state and validated user-entry assembly: GDT selectors, TSS.RSP0, syscall stack, IDT DPL and privilege transition; include ring-3 fault/return tests.
2. Task execution record: PID/parent/status, address-space root, owned kernel stack, saved callee/caller registers, user RIP/RSP, FPU/SIMD policy and teardown ownership.
3. Architecture context switch: atomically save/restore task state and switch kernel stack + CR3; preserve interrupt/preemption invariants. Add two-task register/stack/address-space isolation tests.
4. Process-bound syscall dispatch: caller identity, checked user-pointer copy, GETPID, EXIT/WAIT, READ/WRITE, OPEN/CLOSE/SEEK and error propagation; test invalid pointers and privilege faults.
5. VFS and storage: real ramfs/cpio mount for Live/Recovery, block driver and partition/filesystem mount for Installer, file descriptor lifecycle, read-only /etc/os-release, writable /tmp, and explicit mount failure behavior.
6. Service supervisor: dependency graph, start/health/stop/restart, process reaping and event-driven wakeups. Init must not print readiness before required services independently pass health checks.
7. Target payloads: build distinct production Live, Installer and Recovery init ELFs with shared ABI but target-specific service manifests/policies. Verify ELF machine/type/entry/segment bounds and hashes.
8. GRUB/ISO packaging: pass exactly the selected target's init ELF and target data modules; reject missing, duplicate, wrong-target or hash-mismatched payloads. Include payload hashes in the ISO manifest.
9. SMP only after BSP task lifecycle is real: APIC/ACPI topology, AP startup/trampoline, per-CPU GDT/TSS/syscall stack, per-CPU scheduler queues/locks, reschedule and TLB-shootdown IPIs, remote active-CR3 tracking, deferred frame reclamation and concurrent fault injection.
10. Full acceptance: same ISO SHA across Live/Installer/Recovery × BIOS/UEFI; real nonzero PID, CPL3 syscall trace, VFS OPEN/READ/CLOSE, writable /tmp, Aurora health, installer persistence, recovery postcondition and measured overlapping execution on at least two CPUs. Capture boot traces and hashes; do not substitute host probes.

### 12.3 Latest build and CI state

- Chimera commit 69451fb5a61315e71babcbfd2000a33dc3fdbda8 reformats chimera_sched_snapshot() after Full ISO run 41366732482 failed at -Werror=misleading-indentation. The Full ISO rebuild is run 41367322786; at the last poll, ASM/C/C++ build and ISO composition were still running, and no artifact had been uploaded.
- The matching Chimera CI/CD run 41367322700 had Windows Configure and Build successful; Windows Test was still running at the last poll.
- No Full ISO download link is valid until GitHub reports a non-expired artifact from a successful run. The release-publication step must also pass its target handoff evidence gate.

### 12.4 Release gate

Do not weaken the verifier, add the test-only smoke ELF to production media, synthesize PID/readiness output, or remove native-init exit 78. A successful compile or ISO file is only a build candidate; it is not production acceptance. Keep both PRs draft/unmerged until the complete matrix above passes.

### 12.5 Full ISO candidate trace audit (2026-11-02)

Full ISO run 41367322786 completed the build, ISO payload checks, QEMU kernel boot smoke, trace upload and compressed-artifact upload. The workflow run itself is green because the target acceptance gate is deliberately non-fatal for reviewable candidate builds; the release step was skipped because the gate output was not true. Do not interpret the green workflow result as userspace acceptance.

The uploaded chimera-target-userspace-traces artifact (artifact 13106904729, SHA-256 3c9868bba3dae99f0ea46b6d516fda0244b9913a85e9638a0c6262854a9d43a9) was downloaded and inspected:

- Live trace: initramfs and manifest modules are registered; kernel prints USERSPACE READY withheld because ELF load-plan admission is not a process execution context; target task prints that no executable ring-3 entry path is connected.
- Installer trace: the five installer metadata/image modules are registered; kernel withholds USERSPACE READY; installer task prints that graphical installer userspace is not running and no verified process context/ring-3 transition exists.
- Recovery trace: recovery initramfs and manifest modules are registered; kernel withholds USERSPACE READY; recovery task prints that the repair shell has not been entered.
- All three traces lack USER INIT SYSCALL target/PID and USERSPACE READY target/PID records. None contains a production chimera-user-init-elf module. The three test ISO GRUB configs only pass their respective initramfs/metadata modules.

The Live and Recovery initramfs images do contain shell /init scripts, but those scripts are not executed by the current kernel path; their embedded USERSPACE READY shell output is therefore not present in the QEMU traces and cannot be counted as a native CPL3 init acknowledgement.

Thus the target verifier correctly leaves accepted=false and publication is skipped. The job step is green because it records the false gate and allows candidate artifacts to be uploaded for engineering review; it is not a passing target acceptance result. Full ISO candidate artifact 13107437782 (ZIP containing compressed ISO and checksums) is available from workflow run 41367322786, but it must not be described as a production release.



### 12.6 Truthful boot-state diagnostics

Chimera commit 87458f70367ab6350476d77c957a2019024deeb5 corrects boot diagnostics that previously said installer services were started/in parallel and core storage/security/logging were active even though only declarations existed. Commit 0bd2637f55a12606334f691eadc2ea0eace905f4 adds tests/boot/test_koronos_boot_claims.py, and workflow commit b5c25d0a584ffdca32ad483eaec313a3f41f178e runs it in Full ISO validation.
These changes improve diagnostic integrity only. They do not start services or create a userspace execution path. The native init, VFS/syscall, task-context, per-CPU and SMP gates above remain blocked until their real implementations and runtime evidence exist.


### 12.7 CI after truthful boot-log changes (2026-11-02)

- The first follow-up boot-validation run (41368300847) caught a stale build-script string assertion: kernel/build-koronos.sh still expected the old “Installer runtime initialization” marker after the log was correctly made explicit that installer userspace is not initialized. The assertion was updated in commit 1171a1362609a1b056ea34316a00a129091a24c4 to require the new truthful message (and the new service-declaration message).
- On that commit, Koronos Kernel Build run 41368394157 passed compile, protected-process admission, ELF64 validation and unresolved-symbol checks. ELF64 admission/scheduler regression run 41368394195 passed; transactional ELF loader tests 41368394087 passed; physical mapping tests 41368394075 passed.
- Boot and ISO validation run 41368394173 passed after the stale marker assertion was fixed. Full ISO run 41368394073 was cancelled when a newer PR-head update superseded it. The replacement Full ISO run 41368476616 is currently installing dependencies; the new boot-claims regression is wired into this run but has not yet been verified.
- Latest CI/CD run 41368476612 has Windows Configure passed and Build in progress; Test is pending. Earlier Windows retries were cancelled before completing tests. Do not claim Windows tests passed.


## 12.8 Installer loader blocker re-audit (2026-11-02)

The automatic GRUB selection change does not complete the Installer loader. A source-level re-audit of the current PR head (`863b6b89d5f3400fe226ee3aff468be5d24bdd88`) confirms the following hard boundaries:

- `boot/iso/grub.cfg` selects the Installer menu entry without a timeout and passes the compressed `installation.img` plus installer metadata as Multiboot2 modules. It does **not** pass a module tagged `chimera-user-init-elf`.
- `tools/chimera-stage-installer-media.sh` creates a BusyBox CPIO initramfs with an executable shell script at `/init`. That script mounts devtmpfs/proc/sysfs/tmpfs, invokes the optional shell installer runtime, and falls back to an interactive BusyBox shell. It is an initramfs script, **not** a native ELF process image. The current Koronos boot path does not mount this CPIO image or execute its `/init`.
- `kernel/include/chimera/process_loader.h` explicitly documents that `chimera_elf_load_user_image()` prepares mappings but does not switch to ring 3. `kernel/core/process.cpp` records `CHIMERA_PROCESS_ADMITTED` load-plan records; it does not create runnable CPU contexts.
- `kernel/core/syscall.cpp` has no process-bound filesystem syscall path. GETPID and EXIT/EXIT_GROUP are rejected with ENOSYS in the compatibility dispatcher; only YIELD and TIME_TICKS are handled there.
- `kernel/core/koronos.cpp::task_installer` parses the installer module/metadata phases, then reports that no production init ELF is present and blocks. This is an intentional fail-closed state, not a loader timeout that can be repaired by increasing GRUB timeouts or by adding a shell marker.

### Required implementation before Installer handoff can be called fixed

1. Implement per-CPU GDT/TSS and a validated user-mode entry/return path, with a process-owned kernel stack and saved register context.
2. Turn ELF mapping into a process-creation transaction: own the address space, mapped frames, stack, PID, and rollback on every failure; commit only when a runnable context is complete.
3. Add process-bound syscall dispatch and real VFS/file-descriptor operations needed by init (`OPEN/READ/WRITE/SEEK/CLOSE`), plus writable `/tmp` and a verified `/etc/os-release`.
4. Build a freestanding, architecture-matched Installer init ELF with a defined ABI and no dependency on hosted libc. Package it as a distinct Multiboot2 module (`chimera-user-init-elf`), hash/validate it during ISO construction, and reject a missing or invalid ELF before boot handoff.
5. Implement actual installer service supervision, device/storage discovery, partition/format/copy/bootloader operations, and an explicit destructive-action confirmation policy. A text shell or metadata planner is not the graphical installer.
6. Add QEMU tests proving CPL3 entry, a user-originated syscall, real PID, VFS operations, writable `/tmp`, installer UI/service startup, and persistence on a disposable virtual disk. Exercise BIOS and UEFI using the same ISO SHA.

No native Installer init ELF, process context switch, filesystem syscall implementation, storage-backed installer, or graphical Installer runtime was added by the GRUB-only change. The current Full ISO workflow is still a development-candidate build; its successful packaging status cannot satisfy these runtime acceptance requirements. Keep PR #218 draft and the production release gate closed until the evidence above exists.


## 12.9 x86-64 per-CPU GDT/TSS bootstrap (2026-11-02)

The x86-64 kernel now has a concrete BSP GDT/TSS initialization layer:

- `kernel/include/chimera/x86_64_cpu.h` defines the packed 104-byte 64-bit TSS, GDTR ABI, kernel/user selectors, and TSS descriptor encoder.
- `kernel/core/x86_64_cpu.cpp` owns 16 statically reserved CPU-state slots, each with a private GDT, TSS, and 16-KiB privilege-entry stack. `chimera_x86_64_cpu_init(cpu_id)` builds the ring-0/ring-3 descriptors, sets RSP0, installs the TSS descriptor, and invokes the architecture loader.
- `kernel/arch/x86_64/cpu_state.asm` loads the GDT, reloads kernel data/code selectors, and executes LTR.
- BSP initialization is invoked at the start of `koronos_boot`. The TSS is loaded, but the syscall IDT gate remains DPL0.
- `chimera_x86_64_cpu_set_kernel_stack` provides the later scheduler integration point for replacing the per-CPU entry stack with a process-owned kernel stack. Its caller must run on the owning CPU with interrupts disabled; that ownership/lifecycle integration is not yet implemented.
- Host-side descriptor-layout tests run before the freestanding kernel build.

The kernel build on the initial TSS commit passed, including the new descriptor-layout test and NASM assembly. The first QEMU run exposed that the entry-stack member was not 16-byte aligned; initialization correctly refused to load the TSS. The member now has explicit 16-byte alignment and a compile-time offset assertion. The unused-variable warning was also removed. The new QEMU workflow now requires the explicit BSP GDT/TSS initialization marker; rerun evidence is pending.

**Not completed by this section:** AP startup/per-CPU initialization, process-owned kernel stacks, saved register/trap contexts, CR3 switching, user-mode IRETQ entry/return, syscall frame validation, or VFS/file descriptors. Ring 3 remains disabled and userspace readiness remains withheld until these are implemented and tested together.


## 12.10 Validated CR3 address-space activation primitive (2026-11-02)

The address-space backend now exposes `koronos_address_space_activate`,
`koronos_address_space_restore`, and `koronos_address_space_current_root`.
Activation accepts only an active backend-owned address space; restore accepts
only the bootstrap root or another active backend-owned root. Both reject
unaligned/out-of-range roots, preserve the caller's interrupt-enable state,
and switch CR3 only after validating the root. The address-space self-test now
switches from the bootstrap PML4 to a newly created user address space, verifies
CR3 readback, restores the original root, and verifies restoration before
reclaiming the test address space.

The QEMU boot-matrix and Full ISO target checks now require the explicit
`[MM  ] Address-space self-test passed: CR3 switch/restore` diagnostic in
addition to the BSP GDT/TSS marker. This makes a build that merely compiles the
switch primitive insufficient for this test.

This is still not a process scheduler context switch: no per-process saved
register/trap frame is restored, no process-owned kernel stack is selected by
the scheduler, and no user-mode IRETQ transition is enabled. Ring 3 remains
disabled until those pieces and process-bound syscall/VFS handling are complete.


## 12.11 SVGA boot-display policy (2026-11-02)

All shipped GRUB/Jasper/Spit Fire target menus now request only 800x600 SVGA, with 640x480 as the sole fallback, and set `gfxpayload=keep`. The policy is applied to the primary ISO menu, Jasper root/live/installer/recovery/diagnostics/retro menus, Spit Fire, and the installation menu. This prevents the bootloader from selecting 1024x768, HD, 4K, or an adapter-dependent `auto` mode during boot.

The policy is intentionally retained across the Multiboot2 handoff. It does **not** claim that the final desktop can already switch modes: the current Koronos bootstrap writes to VGA text memory and registers display drivers, but it does not yet provide a verified native GPU modeset/KMS path or a target-readiness-gated resolution transition. Multiboot2's framebuffer handoff describes the current framebuffer; it is not itself a firmware mode-setting API. Keep SVGA active until a real target is healthy, then enable the final desktop mode only after a native display backend can safely modeset and restore the SVGA fallback on failure.

The existing boot-claims regression suite now checks all nine shipped boot-menu configurations for the exact SVGA/fallback mode and `gfxpayload=keep`. QEMU BIOS/UEFI runtime confirmation and target-gated desktop modesetting remain pending; no graphical target readiness or production acceptance is inferred from the configuration test.
