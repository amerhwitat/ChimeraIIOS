# Chimera II OS native live boot

The intended native boot order is:

**BIOS/UEFI → Spit Fire → Jasper (or GRUB2 Multiboot2 fallback) → Koronos → CPIO initramfs/VFS → validated ring-3 target ELF → live, installer or recovery target.**

This ordering follows the broad phase separation used by modern Linux boot (kernel, initramfs, PID 1, services, display server, desktop) and Windows boot (Boot Manager, OS Loader, kernel, Session Manager, Winlogon/services, desktop). These are architectural references only; Koronos does not claim Linux or Windows ABI compatibility.

## What currently runs

- **Koronos x86-64** is the native kernel build/boot target. The x86-64 QEMU matrix validates the kernel boot path.
- **Spit Fire, Jasper and GRUB2** provide the declared boot/menu paths. Menu timeout validation enforces a 300-second interactive wait before default selection.
- **Initramfs/VFS** validates and mounts the selected CPIO newc archive as a read-only root before the target ELF handoff.
- **Live target** is a native ring-3 interactive console with a small set of built-in commands. It is not yet a general-purpose shell or desktop session.
- **Installer target** is a storage-plan dry run. It does not partition, format or write to disks.
- **Recovery target** reports diagnostics and syscall state. It does not repair filesystems or restore installations.
- **Kore, native display server and Aurora graphical desktop** are not yet started by the native Koronos live target.

## Hosted Linux desktop path (separate from native Koronos)

The hosted Chimera II OS and OctavianOS live images use a Linux kernel. They package the real distribution X.Org X Server and Xwayland, plus `startx` and an XDG session dispatcher. `chimera-xserver-session list` discovers installed X11 desktop sessions; `chimera-xserver-session start SESSION_ID` launches a session only when its actual executable is present. Wayland sessions remain owned by their Wayland compositor.

The hosted images also install verified open-source terminal and shell providers, register launchers only for providers that pass executable and smoke checks, and ship Aurora's generated icon artwork, application icons, wallpapers and sound assets. These Linux binaries are not Koronos-native programs.

## Architecture status

- `x86_64`: Koronos kernel build and QEMU boot target.
- `aarch64` and `riscv64`: early entry/UART probes are being added to CI; these are not full kernel ports.
- `x86_32`: serial-only bring-up probe; not a production kernel.

See [boot-sequence.json](boot-sequence.json) for evidence-backed stage statuses and the release-gate list. A production native ISO is not accepted until writable VFS, storage/network/display/audio drivers, PID 1/service lifecycle, native desktop, installer write/rollback and recovery repair are implemented and tested on each claimed architecture.
