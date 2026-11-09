# Koronos boot sequence mapped to current Linux boot architecture

This design uses the current Linux kernel x86 boot protocol, EFI stub, initramfs and systemd bootup documentation as architectural references. It does not claim Koronos implements Linux's kernel ABI or systemd.

## Reference sequence

The current Linux boot model is:

1. BIOS/UEFI firmware performs platform initialization and hands control to a bootloader (or loads a PE/COFF EFI-stub kernel).
2. The bootloader loads the kernel, command line, and optional initrd/initramfs and transfers control using the architecture boot protocol.
3. The kernel validates the handoff, initializes early memory/CPU/interrupt/platform services and interprets the initramfs CPIO archive.
4. An initramfs init process discovers the root device, mounts the real root, and performs a switch-root when required.
5. The system manager starts ordered targets and services, discovers remaining hardware, mounts filesystems, and launches the graphical session.
6. A display server/compositor owns display and input resources; a session manager starts desktop components and applications.

Primary references:
- Linux x86 boot protocol: https://docs.kernel.org/arch/x86/boot.html
- Linux EFI boot stub: https://docs.kernel.org/admin-guide/efi-stub.html
- systemd boot and initrd stages (systemd 261): https://www.freedesktop.org/software/systemd/man/261/bootup.html
- X.Org server and protocol documentation: https://www.x.org/Documentation/
- X Window System client/server concepts: https://www.x.org/guide/concepts/
- Microsoft Windows startup phases: https://learn.microsoft.com/windows/client-management/advanced-troubleshooting-boot-problems
- Microsoft Windows 11 Secure Boot and Trusted Boot: https://learn.microsoft.com/en-us/windows/security/operating-system-security/system-security/trusted-boot

## Windows startup comparison

Microsoft documents the Windows startup stages as PreBoot/firmware, Windows Boot Manager, Windows OS Loader (winload), and the Windows NT kernel. After kernel initialization, control passes to Session Manager (Smss.exe), which initializes sessions and starts remaining drivers and services; user logon and the desktop shell follow.

| Windows phase | Koronos/Aurora analogue | Difference |
|---|---|---|
| UEFI/BIOS PreBoot | Firmware + Spit Fire | Koronos uses its own CHMBOOT1 handoff and architecture bootstrap |
| Windows Boot Manager + BCD | Jasper + Gates/GRUB2 | Menu and boot policy are separate components; 300-second user-choice timeout |
| winload.exe / winload.efi | GRUB2 module loading + Koronos entry | Multiboot2 modules and CHMBOOT1 are not the Windows loader format |
| ntoskrnl + boot drivers | Koronos memory, scheduler and driver bootstrap | x86-64 implementation; driver and SMP coverage remain partial |
| Session Manager (Smss.exe) | Kore bootstrap + selected ring-3 target ELF | Not a full PID-1/session manager or Windows process subsystem |
| Winlogon / desktop shell | Aurora session manager and desktop | Hosted Linux desktop only; native Koronos GUI remains a release gate |

The Windows analogy is architectural only. It does not mean Koronos implements the Windows kernel ABI, BCD, PE loader, Winlogon, or Windows driver model.

## Koronos mapping

| Linux stage | Chimera/Koronos component | Current implementation boundary |
|---|---|---|
| Firmware | BIOS / UEFI | CHMBOOT1 records firmware and platform data; architecture support is not yet universal |
| Bootloader | Spit Fire → Jasper → GRUB2/Gates | x86 BIOS/UEFI/Multiboot2 boot path; visible 300-second menu |
| Kernel entry | Koronos | Validates boot context, scans Multiboot2 modules, early console |
| Early kernel | Physmap, frame allocator, address-space manager, scheduler | x86-64 implementation; process and SMP support remain partial |
| Initramfs | CPIO newc + Koronos read-only VFS | Transactional CPIO mount; /init and /bin/busybox are required before ring-3 handoff |
| Init process | target-init-live / installer / recovery ELF | Explicit Multiboot2 ring-3 ELF target; Koronos does not yet interpret /init shell scripts or execute an ELF directly from the CPIO VFS |
| System manager | Kore | Bootstrap service registration exists; full dependency graph, restart policy, IPC and service supervision remain incomplete |
| Device discovery | PCI, firmware, driver manager | Several registries and drivers exist; production hardware coverage and binding tests remain incomplete |
| Networking | Spotnik | Partial; no claim of full Linux-compatible sockets stack |
| Display server | X.Org on hosted Linux; Wayland compositor on hosted Linux | The hosted images package X.Org/Xwayland and Aurora Wayland. A native Koronos X server is not yet implemented because Koronos still needs production framebuffer/DRM, input, IPC and socket APIs |
| Desktop session | Aurora | Hosted Linux has Aurora WebKit kiosk, Wayland session, X.Org fallback, shell/terminal launchers and app icons. Native Koronos graphical session is not yet production-ready |

## Required ordering and fail-closed rules

- Validate boot context and module bounds before using any module address.
- Establish physical-memory ownership and user page-table isolation before ring-3 admission.
- Mount and validate the selected target's CPIO initramfs before launching the selected target ELF.
- Require a regular /init and /bin/busybox in the CPIO tree. A failed mount or missing required file blocks userspace handoff.
- Admit exactly the target ELF selected by Jasper/GRUB (live, installer, or recovery) and require the kernel's own readiness acknowledgement.
- Start service targets only after the kernel/process prerequisites they depend on are available.
- Start the native graphical session only after the kernel has working display, input, IPC and graphics services. A hosted X.Org/Xwayland package is not a Koronos-native display server.
- If a phase fails, remain in diagnostics/recovery; never report desktop readiness from menu progress or package presence alone.

## Release gates

A Koronos-native production ISO requires all of the following to pass on each claimed architecture:
- Firmware/bootloader handoff and module validation in QEMU plus physical hardware where available.
- Kernel build, memory ownership, page-table, syscall, scheduler, process and SMP tests.
- Valid live, installer and recovery CPIO VFS mounts and ring-3 target launch/readiness.
- A functional writable storage VFS, real installer partition/filesystem operations, rollback and recovery.
- Device discovery and working display/input/audio/network drivers.
- Native display server/compositor and Aurora desktop runtime.
- Command and ISA conformance for every advertised native implementation.

The Debian/Linux-backed Chimera and Octavian live images are separate hosted editions. Their X.Org, Mesa, Xwayland and Linux package binaries do not prove Koronos-native support.