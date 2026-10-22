# Native init integration status

Updated: 2026-10-22

This branch now contains a dedicated freestanding native init source at `kernel/userspace/native_init.c` and an ELF linker layout at `kernel/userspace/native_init_linker.ld`. The kernel build emits target-specific `native-init-live.elf`, `native-init-installer.elf`, and `native-init-recovery.elf` artifacts with explicit RX and RW PT_LOAD checks. These artifacts are independent of candidate smoke probes.

**They are not yet staged into production GRUB entries in this branch.** Inspection of the current ChimeraIIOS kernel build graph found that this branch does not contain the native ring-3 launch path present in the OctavianOS vendored kernel: `address_space.cpp`, `frame_allocator.cpp`, `target_launch.cpp`, `user_entry.asm`, and their headers are absent from the build graph/tree. Staging the native ELF before porting that execution backend would produce an ISO that merely carries an ignored module and would not fix the verifier failure. GRUB was therefore kept unchanged and the ISO builder does not claim native-init integration.

The native init currently proves only a minimal process/syscall handshake: DPL3 `INT 0x80`, kernel-owned PID retrieval, target-specific readiness write with a checked return value, and native exit. It does **not** implement or claim VFS mounting, CPIO file lookup, storage durability, service supervision, or desktop readiness. Those must be implemented and tested before the system-level release gate can pass.

Required next porting work for ChimeraIIOS:
1. Port and integrate the real address-space/frame allocator, ELF load/permissions, TSS/ring-3 entry, syscall lifecycle, and target launch backend.
2. Only then stage the three native-init artifacts in production GRUB and pass the initramfs/installer payload as separate data modules.
3. Add a real VFS/data-archive interface and make native init check it before emitting target readiness.
4. Run the unchanged production verifier across Live/Installer/Recovery × BIOS/UEFI; keep PR/release blocked until all cases pass.
