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

The policy is intentionally retained across the Multiboot2 handoff. It does **not** claim that the final desktop can already switch modes: the current Koronos bootstrap writes to VGA text memory and registers only a generic VGA display descriptor; it does not parse the Multiboot2 framebuffer tag into a pixel console, provide a verified native GPU modeset/KMS path, or implement a target-readiness-gated resolution transition. Therefore on-screen kernel text after GRUB hands off is not yet guaranteed to remain visible in the SVGA graphics framebuffer (serial/debugcon diagnostics remain available). Multiboot2's framebuffer handoff describes the current framebuffer; it is not itself a firmware mode-setting API. The next graphics dependency is a validated framebuffer text/progress console, followed by a native display modeset backend. Keep SVGA active until a real target is healthy, then enable the final desktop mode only after that backend can safely modeset and restore the SVGA fallback on failure.

The boot-claims regression suite checks all nine shipped boot-menu configurations for the exact SVGA/fallback mode and `gfxpayload=keep`; `kernel/build-koronos.sh` now runs that suite before compiling Koronos. QEMU BIOS/UEFI runtime confirmation, framebuffer-console visibility, and target-gated desktop modesetting remain pending; no graphical target readiness or production acceptance is inferred from the configuration test.


## 12.12 Shared language, compiler, assembler and disassembler catalog (2026-11-02)

The canonical `toolchains/language-toolchain-catalog.json` now records 66 language/runtime families, 13 assembler providers and 11 disassembler/reverse-engineering providers. New entries cover V, Odin, experimental Carbon, MATLAB and GNU Octave, Wolfram Language, SAS, Raku, Elm, Haxe, Reason/ReScript, Solidity, Vyper, Move, Verilog, SystemVerilog and VHDL. The catalog includes provider command hints, execution models, target/format metadata, licensing boundaries and explicit opt-in package profiles. A new `hardware-description` profile describes Icarus Verilog, Verilator, GHDL and Yosys.

The catalog explicitly declares a common `CHM-LANGUAGE-TOOLCHAIN-1` integration contract for ChimeraIIOS and OctavianOS. Octavian's vendor copies of the catalog, matrices, validator, tests, Aurora profile metadata, SDK manual and CI workflows are byte-for-byte synchronized with the Chimera branch. Native Toolchain CI run 41376280252 passed: the validator reported 66 languages, 13 assemblers and 11 disassemblers; all four catalog regression tests passed; native C/C++/ASM linker conformance passed; CMake built Chimera assembler, disassembler and reverse-engineering tools.

This is a provider capability catalog and optional package-plan integration, not a claim that all 66 language toolchains are bundled or that all providers run on the native Chimera ABI. Proprietary MATLAB, Wolfram, SAS, MASM, ARM Compiler, IAR and Apple tools remain externally installed under their licenses. Carbon is experimental. Actual provider availability and target ABI/runtime compatibility must be verified separately.

## 12.13 Interactive GRUB timeout and QEMU smoke-test correction (2026-11-02)

The latest Full ISO run before the timeout correction (41375361717) passed ASM/C/C++ build and ISO composition, ISO artifact validation, and embedded target payload/artwork checks. The QEMU smoke test then terminated after 20 seconds with an empty debugcon trace. The shipped GRUB menu had deliberately been changed back to a 30-second interactive Live-first menu. Because the QEMU timeout was shorter than the GRUB countdown, the VM was terminated before selecting a boot entry; this was a test harness timeout mismatch, not evidence of a kernel exception.

Both `.github/workflows/chimera-full-iso.yml` and `.github/workflows/koronos-boot-matrix.yml` now allow 60 seconds for QEMU, retaining the interactive menu rather than changing production boot policy. On the latest branch head `620a1b9fa69cb54d3b5abfe735c2f4ce60779aa9`, Koronos Kernel Build run 41376510340 passed, Boot Artifact Validation run 41376510225 passed, Runtime Contracts run 41376510233 passed, and the ISA/installer/command conformance run 41376510197 passed. The new Full ISO run 41376510227 is pending; the two-CPU boot-matrix run 41376510275 is still running. The timeout fix has not yet been validated by a completed QEMU run.

The 60-second timeout fixes only the harness/menu timing mismatch. It does not prove a CPL3 handoff, a working Live/Installer/Recovery userspace, storage persistence, or publication. Keep the production release gate fail-closed.


## 12.14 QEMU boot-matrix confirmation after interactive-menu timeout fix (2026-11-02)

The 60-second QEMU timeout is now exercised successfully by Koronos VMware/QEMU Boot Matrix run 41376751858. Its x86_64 boot job completed successfully, including Koronos build, desktop artifacts, minimal Multiboot2 ISO creation, and QEMU serial/debugcon boot smoke. The captured trace confirms:

- `[CPU ] BSP GDT/TSS initialized; ring-3 entry remains disabled pending process contexts`
- `[MM  ] Address-space self-test passed: CR3 switch/restore, kernel identity mappings, user U/RW/NX permissions and frame rollback verified`
- `[KRN ] KORONOS READY`
- `[USER] USERSPACE READY is withheld: ELF load-plan admission is not a process execution context`
- `[CPU ] Online scheduler CPUs: 1 (AP startup not implemented)`

This confirms the BSP TSS load and CR3 address-space primitive execute in QEMU, not just host-side descriptor tests. It does **not** demonstrate CPL3 execution, process-owned kernel stacks, process context switching, VFS, init PID, desktop readiness, or SMP. The diagnostic artifact is [run 41376751858 / artifact 13112115406](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41376751858/artifacts/13112115406).

Octavian's final vendored boot-routing validation after synchronizing the missing live/full builder scripts and original Chimera wallpaper/manifest passed in run 41376946110, including language catalog validation, GRUB parsing, target graph, installer routing, ISO payload validator, splash contracts, shell syntax and desktop companion smoke. Earlier partial-sync failures were superseded by this final-head success.

The latest Full ISO workflow run 41376751779 remains pending at this ledger update. ISO composition and target-specific Live/Installer/Recovery handoff on the final head are therefore not yet verified. The production release gate remains closed.


## 13. CI and trace revalidation — 2026-11-02 (latest observed)

### ChimeraIIOS PR #218 candidate

- Full ISO workflow [41377107501](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41377107501) completed the freestanding build, ISO composition, payload/artwork validation, QEMU boot smoke, trace collection and ISO artifact upload. Candidate artifact: [13111808525](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41377107501/artifacts/13111808525). Target trace artifact: [13111368542](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41377107501/artifacts/13111368542).
- The three captured target traces are explicit non-acceptance evidence: Live says the initramfs is registered but no executable ring-3 entry path is connected; Installer says no verified process context/ring-3 transition; Recovery says the repair shell has not been entered. The traces also confirm BSP GDT/TSS initialization and CR3 switch/restore self-test, while explicitly withholding user readiness.
- The workflow can complete as a candidate build while keeping its publication step skipped. Its green build result must not be described as a production userspace pass or as the six-case immutable-ISO acceptance matrix.
- On this candidate, core service logs now state that service identities are registered and storage/security/logging backends are declared but not running. This is the required truthful state.

### OctavianOS PR #145 candidate

- Native Koronos compilation, ELF/Multiboot2 validation, scheduler runtime regression, module classification tests, QEMU kernel readiness, initramfs composition and candidate ISO upload completed successfully in [run 41377614672](https://github.com/amerhwitat/OctavianOS/actions/runs/41377614672). Candidate ISO artifact: [13111962681](https://github.com/amerhwitat/OctavianOS/actions/runs/41377614672/artifacts/13111962681); kernel ELF artifact: [13111833006](https://github.com/amerhwitat/OctavianOS/actions/runs/41377614672/artifacts/13111833006).
- The separate full-ISO production handoff verifier in that run failed for Live, Installer and Recovery: all three traces lacked a user-originated CPL3 init syscall acknowledgement and actual init PID readiness marker. Prerelease publication was skipped.
- The separate six-case candidate probe workflow [41377614738](https://github.com/amerhwitat/OctavianOS/actions/runs/41377614738) completed 6/6. These are target-routing/test-init probes, not the production init/service payloads, and do not override the failed full-ISO handoff verifier.
- PR #145 contains a scheduler correctness/truthfulness fix only. The parallel API remains fail-closed; the serial range helper is explicitly sequential. This is not AP startup or SMP scheduling.

### Windows and release state

- Chimera CI/CD run [41377107596](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41377107596): Linux build/tests and infrastructure/code-generation jobs completed successfully; Windows Configure and Build passed, while the Windows Test step was still running at the last poll.
- Keep PRs #217/#218 and Octavian PR #142 as drafts. Do not merge or publish based solely on host tests, QEMU kernel readiness, candidate probes, or ISO artifact creation.
- The production dependency order remains: process-owned guarded kernel stacks and saved trap contexts; architecture context switch with CR3 ownership; timer/preemption and real blocking/wait/exit/reap; AP startup and per-CPU workers; IPI TLB shootdowns/deferred reclamation; process-bound VFS/initramfs/syscalls and production init/service supervision; framebuffer and readiness-gated modesetting; then six production BIOS/UEFI cases on one immutable ISO SHA.
- Native-init exit 78 and all fail-closed gates remain unchanged.


## 14. Latest CI queue and scheduler-claim cleanup — 2026-11-02

The final Koronos build banner was corrected to identify the BSP scheduler callback runner and explicitly state that no SMP execution is present (commit `a5be7d9419b1e8208015347879265d19ba9e96a0`). New Full ISO validation run 41378389423 is pending. CI/CD run 41378389406 has its Linux build/tests, code generation and infrastructure validation completed successfully; Windows CI is still in progress. This is a diagnostic accuracy change only. It does not implement AP startup, independent per-CPU scheduler workers or overlapping task execution.


## 15. Immutable ISO identity check on target traces — 2026-11-02

The target trace artifact 13111368542 from Full ISO candidate run 41377107501 contains three separately composed target-specific test ISOs. Their SHA-256 values are:

- Live target test ISO: `78e7d431f2af571fc87042023e51e60014230f7e8ed5a60a347d6c3f2ca691a1`
- Installer target test ISO: `f77a0ac4569ec0061157a803e512071398d24ce73e4c96f2b6d8d253da0f3460`
- Recovery target test ISO: `ab38b559f11a80697b36ba06421a7085dc6b2c0393ece73f7a8f3b800e5e4a4b`

These are three different hashes. The artifact therefore cannot be used as evidence that BIOS and UEFI Live/Installer/Recovery all booted from one immutable ISO SHA. It remains useful for target-specific diagnostic traces only. The six-case same-ISO production acceptance requirement remains unmet.

The boot-claims regression test was also extended to assert BSP-only scheduler initialization and the truthful build banner (commit `e4eff82e26be219e4f61c806806c4c262757d78e`). Revalidation run 41378733537 and related checks were queued/in progress at the time of this ledger update.


## 12.9 Guarded shared kernel stacks and process ownership bridge (2026-11-02)

Implemented on the current memory-foundation branch:

- Address-space initialization allocates a shared supervisor-only high-half page-table subtree at PML4[511]. The bootstrap root owns it, and each newly created process root inherits the same subtree. Other unknown higher-half entries remain rejected.
- A bounded 32-slot arena provides one unmapped guard page below eight supervisor writable/NX pages per stack. Stack allocation maps physical frames with rollback on partial failure; release checks that no initialized CPU has the stack top installed as TSS.RSP0.
- Process records now support attaching, retrieving and detaching a guarded-stack handle. A separate process-stack bridge creates and releases stacks while preserving the handle if release is refused.
- The boot self-test verifies guard absence, visibility through a second address-space root, and BSP TSS.RSP0 install/restore. It is not a task switch and does not prove the current task has stopped executing on the stack.

Validation on head `4906080184df934318adfaee26b02925eee78b91`:
- Koronos Kernel Build run [41397184627](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41397184627): PASS.
- QEMU VMware/boot matrix run [41397184684](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41397184684): PASS; trace contains the exact guarded-stack/TSS self-test success line and KORONOS READY.
- ELF process-loader unit tests and frame-allocator host tests: PASS.
- Windows CI/CD run [41397184702](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41397184702): Windows Build and Test PASS.

Implemented on the BSP: cooperative kernel-callback contexts use guarded stacks and saved RSP/register frames, with TSS.RSP0/current-PID handoff. The architecture wrapper now adds a BSP-only cross-CR3 path over the shared supervisor stack subtree; exact-head QEMU validation for this new path is pending. Still not implemented: native user-process context construction/dispatch, IRETQ entry/return, timer preemption, process wait/reap, AP startup, inter-processor TLB shootdowns, and deferred address-space reclamation. Mapping mutations remain BSP-only. The process-stack bridge is not automatically invoked by ELF admission. Keep native-init exit 78 and all production release gates fail-closed.


## BSP guarded-stack context handoff (2026-11-02)

The guarded-stack implementation now has a BSP context-switch wrapper around the x86-64 assembly stack-frame exchange. With interrupts disabled, the wrapper validates the target address-space root and verifies that the target RSP is within the eight mapped supervisor RW/NX pages in that root (with the adjacent guard page still unmapped), or is the immutable BSP bootstrap stack. It records the outgoing CR3, TSS.RSP0 and PID, performs a local CR3 write when roots differ, installs the target RSP0/PID, then executes the assembly stack-frame switch. The shared PML4[511] supervisor subtree keeps guarded task stacks mapped in both address spaces. The switch refuses cross-CR3 operation if any AP is online; no cross-CPU TLB shootdown is implied.

The raw assembly primitive now verifies that the wrapper has already activated the target CR3 and preserves the outgoing CR3 stored by the wrapper. A local CR3 write flushes the BSP's translations in the current non-PCID configuration. This is a BSP-only context handoff, not SMP-safe address-space reuse: AP startup, acknowledged TLB shootdowns and deferred reclamation remain unimplemented. The QEMU boot-matrix has been updated to require a real guarded cross-CR3 saved-context/TSS.RSP0/PID round trip. Exact-head validation of this new path is pending.

The cooperative scheduler already switches BSP kernel callback tasks onto their owned guarded stacks and back to its scheduler stack; yield/block/exit resume the saved kernel continuation, and exited callback stacks are released only after the scheduler regains control. It still does not select native process records or run their distinct address spaces. There is no user IRETQ entry/return, timer preemption, process wait/reap lifecycle, or CPL3 syscall return. Process admission still does not automatically attach its runtime to the callback scheduler. VFS file syscalls, writable /tmp, production init/service supervision, AP startup/SMP and six-case same-ISO acceptance remain blocked. Keep native-init exit 78 and all release gates intact.


## BSP guarded-stack scheduler callback execution (2026-11-02)

The kernel build now enables a BSP-only guarded-context mode for the existing cooperative callback scheduler. Each submitted kernel callback receives an eight-page guarded kernel stack. Dispatch prepares an initial saved context, switches from the scheduler stack into the task stack, validates at entry that RSP lies within the owned stack and that TSS.RSP0/current PID match the selected task, executes the callback, and switches back to the scheduler. Exited callbacks release their stack only after returning to the bootstrap scheduler stack. QEMU diagnostics expose dispatch/fault counters, and the boot-matrix now requires the successful stack/TSS/PID trace.

This is **kernel callback context execution**, not user-process scheduling. Kernel callback contexts are now preserved across cooperative yield/block: the saved context resumes at the call site when selected again or woken. A callback that returns or explicitly exits becomes EXITED, and its stack is released after control is back on the scheduler stack. This is still not a user-process continuation, timer-preemptive scheduler, process wait/reap lifecycle, CPL3 transition or process-owned CR3 selection. The scheduler is still BSP-only; parallel execution remains fail-closed and AP startup/TLB shootdowns are absent. Validated on head 37ab44f1d80f8b8934e9d3d729a98a7f8febe376: Koronos Kernel Build run 41417399132 passed (freestanding link, host scheduler/context tests, ELF validation and no unresolved symbols), and QEMU boot run 41417399060 passed. Its debugcon trace explicitly records the BSP callback executing on its owned guarded stack with matching TSS.RSP0/PID, with no context-fault marker. This is a single QEMU serial smoke configuration, not the six-case BIOS/UEFI production matrix.
## Consolidated runtime status — 2026-11-02 (supersedes earlier point-in-time sections)

This section is the current implementation/evidence snapshot. Historical sections above record the state at the time of each earlier change and must not be read as the latest state.

### Implemented foundation (BSP-only; not production userspace)

- **Shared supervisor stack mappings:** a supervisor-only PML4 subtree is shared with newly created address spaces. The stack arena has 32 slots; each slot has one unmapped guard page followed by eight supervisor RW/NX pages. Stack mapping mutation is BSP-only.
- **Process-owned guarded kernel stacks:** the guarded-stack allocator validates generation-tagged handles, rolls back partial allocations, rejects release while a CPU TSS owns the stack top, and is connected to the freestanding transactional ELF process-load path. The process release path drops the guarded stack before destroying its owned address space and retains ownership if stack release fails.
- **BSP TSS handoff:** saved-context switching validates backend-owned roots and the target guarded-stack mapping, disables interrupts while changing the local CR3/TSS.RSP0/current-PID tuple, and restores the outgoing tuple on pre-switch failure. Cross-CR3 switching is restricted to the BSP and refused if any AP is initialized. This local CR3 switch is not a multi-CPU TLB-shootdown protocol.
- **Cooperative kernel callback contexts:** the BSP scheduler allocates a guarded stack per callback, prepares a saved context, checks the active RSP/TSS.RSP0/PID on first entry, and switches back to a dispatcher continuation on yield/block/exit. Exited callback stacks are released after returning to the dispatcher. This is kernel callback scheduling, not user-process scheduling or preemptive scheduling.
- **Process-load state remains fail-closed:** loading an ELF and owning its address space/guarded kernel stack does not make it runnable. READY/RUNNING/BLOCKED remain rejected until a validated user trap frame and IRETQ entry/return path exist.

### Still not implemented or not accepted

- Validated initial CPL3 trap frame, IRETQ user entry/return, process-bound syscall identity, and production Live/Installer/Recovery init ELFs.
- Process wait/parent notification/reap and safe process teardown after asynchronous CPU use.
- Timer preemption, interrupt-driven blocking/wakeup integration, AP startup, independent per-CPU scheduler contexts, reschedule IPIs, acknowledged TLB shootdowns and deferred address-space reclamation.
- Process-bound VFS OPEN/READ/WRITE/SEEK/CLOSE, mounted root filesystem, writable /tmp, and production service supervision.
- Full BIOS/UEFI × Live/Installer/Recovery acceptance on one immutable ISO SHA, including nonzero PID/CPL3 syscall proof, installer persistence, recovery repair, Aurora/Marine runtime health and verified SMP overlap.

### Verification boundary

The saved-context frame and guarded-stack/TSS/cross-CR3 self-tests are foundation tests, not proof of user-process execution. The latest QEMU scheduler wake/resume assertion failed before the dispatcher-continuation fix; exact-head QEMU revalidation after that fix is pending. Octavian must pass its own native workflow on its own vendored source head; Chimera results are not Octavian evidence. Keep PRs unmerged and production publication disabled until the relevant exact-head tests and six-case acceptance pass. Preserve native-init exit 78 and do not promote test-only init payloads.