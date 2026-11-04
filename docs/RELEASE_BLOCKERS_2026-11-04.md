# Native Koronos release blockers — 2026-11-04

This note records the current implementation boundary. It is deliberately fail-closed: a successful kernel build, ELF probe, desktop build, or ISO checksum is not production acceptance.

## Corrected packaging-to-kernel handoff

The kernel already has a bounded ELF loader, process admission, address-space creation, an x86-64 CPL3 entry path, a DPL3 `INT 0x80` acknowledgement path, PID/CR3 validation, user-originated readiness checking, and a native exit return path.

The production target ELFs are built by `kernel/build-koronos.sh`. The ISO composition path previously failed to stage them as Multiboot2 `USER_INIT_ELF` modules, even though GRUB target entries referenced those files. Consequently, the native launcher found no selected user init and did not enter CPL3.

The ISO builders now stage and validate:

- `/boot/targets/target-init-live.elf`
- `/boot/targets/target-init-installer.elf`
- `/boot/targets/target-init-recovery.elf`

GRUB target entries pass the corresponding `chimera-user-init-elf target=<target>` module command line. The full ISO extraction check verifies the three ET_EXEC files, executable PT_LOAD segments, and the matching GRUB module declarations. Multiboot module classification tests now cover all three target-specific user-init module forms.

This is an integration correction, not yet a runtime acceptance result. Exact-head QEMU and ISO workflows must pass before this path is treated as working.

## Remaining blockers

### Native VFS and syscall surface — BLOCKED

The native user syscall dispatcher currently supports the narrow target-init ABI: GETPID, YIELD, TIME_TICKS, console WRITE, and EXIT. It does not implement a kernel VFS or the OPEN/READ/SEEK/CLOSE filesystem syscall path. No verified root mount, `/etc/os-release` read round-trip, or writable `/tmp` round-trip exists for the native target process.

The Linux live initramfs and its shell are not evidence of native Koronos VFS integration.

### Process and service lifecycle — PARTIAL / BLOCKED

The selected init can be admitted, loaded into an owned address space, run at CPL3, and have its address space reclaimed after exit/timeout. The process record receives RUNNING and EXITED/FAULTED state transitions.

This is not a complete process lifecycle: there is no demonstrated general scheduler-owned context switch across process address spaces, wait/reap contract, deferred process destruction, or production service manager lifecycle. The cooperative scheduler still dispatches callbacks.

### Real SMP — BLOCKED

The scheduler explicitly keeps `chimera_sched_run_parallel()` fail-closed and returns zero until AP startup, per-CPU workers, and reschedule/IPI paths exist. CPU feature enumeration or a QEMU `-smp 2` setting is not proof that two CPUs are online or executing concurrently.

Required evidence remains distinct APIC identities for at least two online CPUs and a measured overlapping execution interval on those CPUs.

### Installer and Recovery postconditions — BLOCKED

The native Installer target is a storage-plan dry run and does not write a disk or install an OS. The native Recovery target emits diagnostics and performs no repair. Therefore no installer cold-boot persistence token or recovery repair transaction/postcondition can be claimed.

### Desktop readiness — BLOCKED for native Koronos

The native Live init is a text-console payload, not an Aurora or Marine graphical session. Desktop builds and Linux live-edition GUI tests do not establish native Koronos desktop readiness. Real per-profile desktop readiness traces are still required.

### Immutable six-case matrix — BLOCKED

`tools/boot/verify-six-case-matrix.py` requires exactly one case for each Live/Installer/Recovery × BIOS/UEFI pair. Every case must attest the SHA-256 of the same immutable ISO and contain ordered CPL3/PID, VFS, and real-SMP evidence. Live also requires Aurora and Marine traces; Installer and Recovery require their matching cold-boot/repair postconditions.

Separate per-target probe ISOs are diagnostic tests only and cannot satisfy this release gate.

## Publication policy

Keep PRs draft and release publication disabled until exact-head SDK/desktop builds, complete ISO build/checksum/extraction, BIOS and UEFI boots, Live/Installer/Recovery runtime, CPL3/PID, VFS, genuine SMP, installer persistence, recovery repair, desktop readiness, and all six same-ISO cases pass.

Do not change the native-init fail-closed exit 78 policy, synthesize readiness, promote test ELFs, or treat documentation/build-only results as production acceptance.
