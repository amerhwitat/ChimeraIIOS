# Jasper / GRUB 2 / Gates boot targets

The live ISO exposes four explicit boot targets in the GRUB 2 menu:

- **Live desktop** — Linux live-boot, Aurora desktop, verbose kernel/systemd output.
- **Installer** — enters the installer session dispatcher. It launches Calamares only when an OS-specific settings file is present. Otherwise it reports that installation is not configured and opens a shell without modifying disks.
- **Koronos** — GRUB `multiboot2` handoff to `/boot/koronos.elf`, but only when a validated Multiboot2 x86-64 ELF is supplied to the ISO build through `KORONOS_ELF=/path/to/koronos.elf`. The target remains visible when no kernel is bundled and reports the missing artifact.
- **Recovery** — boots the Linux live environment into a read-only-first recovery menu. Filesystem repair requires an explicit block-device path and typed confirmation.

The default GRUB graphics mode prefers 1920x1080 and descends through common SVGA/WXGA modes to automatic detection. `gfxpayload=keep` requests that GRUB preserve its framebuffer through the Linux kernel handoff. Firmware and graphics hardware may expose a lower mode; the ISO cannot force a resolution unsupported by the machine or firmware.

Boot output is deliberately verbose: `loglevel=7`, `ignore_loglevel`, `printk.time=1`, systemd status output, both tty and serial consoles, and no `quiet` argument. A serial log is available at 115200 baud.

This is boot-menu and Linux-live-mode integration. It does not itself prove native Koronos boot, production installation, or physical-hardware compatibility. The Koronos handoff is enabled only by a real Multiboot2-compatible kernel artifact. The installer target refuses to perform destructive installation until a matching OS-specific Calamares configuration and installation modules are included.
