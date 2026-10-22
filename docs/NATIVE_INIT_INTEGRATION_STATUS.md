# Native init integration status

Updated: 2026-10-22

This branch now contains a dedicated freestanding native init source at `kernel/userspace/native_init.c` and an ELF linker layout at `kernel/userspace/native_init_linker.ld`. The kernel build emits target-specific `native-init-live.elf`, `native-init-installer.elf`, and `native-init-recovery.elf` artifacts with explicit RX and RW PT_LOAD checks. These artifacts are independent of candidate smoke probes.

**They are not yet staged into production GRUB entries in this branch.** Inspection of the current ChimeraIIOS kernel build graph found that this branch does not contain the native ring-3 launch path present in the OctavianOS vendored kernel: `address_space.cpp`, `frame_allocator.cpp`, `target_launch.cpp`, `user_entry.asm`, and their headers are absent from the build graph/tree. Staging the native ELF before porting that execution backend would produce an ISO that merely carries an ignored module and would not fix the verifier failure. GRUB was therefore kept unchanged and the ISO builder does not claim native-init integration.

The native init source currently describes a minimal process/syscall handshake: DPL3 `INT 0x80`, kernel-owned PID retrieval, a target-payload validation syscall, target-specific readiness write with a checked return value, and native exit. In this Chimera branch, syscall ID 17 is reserved in the ABI header but its process-bound kernel handler and ring-3 launch path are not implemented; therefore the artifact is buildable but not executable here. It does **not** implement or claim VFS mounting, CPIO file lookup, storage durability, service supervision, or desktop readiness. Those must be implemented and tested before the system-level release gate can pass.

Required next porting work for ChimeraIIOS:
1. Port and integrate the real address-space/frame allocator, ELF load/permissions, TSS/ring-3 entry, syscall lifecycle, and target launch backend.
2. Only then stage the three native-init artifacts in production GRUB and pass the initramfs/installer payload as separate data modules.
3. Add a real VFS/data-archive interface and make native init check it before emitting target readiness.
4. Run the unchanged production verifier across Live/Installer/Recovery × BIOS/UEFI; keep PR/release blocked until all cases pass.


## Cross-edition propagation: Mobile edition and ISO/Flash tool — 2026-10-22

The native-init contract must stay aligned with OctavianOS and the public ISO/Flash Center, but Mobile and flash workflows have separate acceptance gates. This is a status/engineering contract; it does not imply those integrations have passed runtime verification.

- **ABI and manifest parity:** synchronize native-init artifact names, target identifiers, module aliases, payload-manifest schema, and user-originated readiness markers with OctavianOS. Keep this branch fail-closed: syscall ID 17 being reserved is not an implemented handler, and staging a module without a ring-3 launcher is not integration.
- **Mobile edition:** reuse shared target/manifest contracts only where applicable; use architecture-specific kernel, boot chain, device profiles, input/touch, display, audio, storage, and compositor implementations. Build and runtime-test each declared mobile architecture/device profile independently. Do not infer Mobile readiness from x86_64 BIOS/UEFI ISO results or desktop UI contracts.
- **ISO/Flash Center:** preserve non-destructive inspection/checksum operations separately from destructive writes. Flash execution must require explicit confirmation (CHIMERA_FLASH_CONFIRM=YES), a validated image, and an unambiguous /dev/... target; reject arbitrary shell execution and verify the result after writing. UI/API contract tests cannot prove that a flashed device boots or that installed data survives reboot.
- **Current implementation boundary:** this branch builds three native-init ELF artifacts, but the matching ring-3 launch backend and process-bound syscall-17 handler are absent here. Do not stage these ELFs into production GRUB routes until the execution path exists and is verified. No VFS mount/file lookup, durable write/readback, service supervision, Aurora handoff, or real AP-backed SMP is established by the artifact build alone.

### Required synchronized verification

- [ ] Cross-repository ABI/manifest parity tests pass for ChimeraIIOS, OctavianOS, and site metadata.
- [ ] Mobile build/runtime matrix passes for each supported architecture/device profile, with unsupported services explicit.
- [ ] Flash Center tests cover cancellation, invalid/corrupt images, invalid/ambiguous device paths, write failures, and post-write verification; no test writes to a real device.
- [ ] All six real production ISO target/firmware combinations pass CPL3-originated acknowledgement and PID-bound readiness checks.
- [ ] Filesystem, persistent storage, installation/reboot, Recovery repair, Aurora handoff, settings/service providers, and AP concurrency are independently demonstrated before release.
