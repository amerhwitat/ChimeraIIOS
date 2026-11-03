# Jasper / GRUB 2 / Gates boot targets

The live ISO exposes four explicit boot targets in the GRUB 2 menu:

- **Live desktop** — Linux live-boot, Aurora desktop, verbose kernel/systemd output.
- **Installer** — enters the installer session dispatcher. It launches Calamares only when an OS-specific settings file is present. Otherwise it reports that installation is not configured and opens a shell without modifying disks.
- **Koronos** — GRUB `multiboot2` handoff to `/boot/koronos.elf`, the ISO builder compiles the repository's native kernel and embeds it after validating its ELF64 x86-64 header and Multiboot2 header. An externally built kernel can override the default with `KORONOS_ELF=/path/to/koronos.elf`.
- **Recovery** — boots the Linux live environment into a read-only-first recovery menu. Filesystem repair requires an explicit block-device path and typed confirmation.

The default GRUB graphics mode prefers 1920x1080 and descends through common SVGA/WXGA modes to automatic detection. `gfxpayload=keep` requests that GRUB preserve its framebuffer through the Linux kernel handoff. Firmware and graphics hardware may expose a lower mode; the ISO cannot force a resolution unsupported by the machine or firmware.

Boot output is deliberately verbose: `loglevel=7`, `ignore_loglevel`, `printk.time=1`, systemd status output, both tty and serial consoles, and no `quiet` argument. A serial log is available at 115200 baud.

The build includes a native Koronos Multiboot2 ELF, and QEMU acceptance checks its early 32-bit → long-mode → kernel-entry → idle-loop debug markers. That is not the same as CPL3 userspace readiness or a production Koronos release. The installer target refuses to perform destructive installation until matching OS-specific Calamares settings and install modules are included. Physical-machine boot remains a separate acceptance gate.
