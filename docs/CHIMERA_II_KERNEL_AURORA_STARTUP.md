# Chimera II Kernel → Aurora Startup

## Scope

This document defines the supported Linux host startup path for the current Chimera II research kernel and Aurora Wayland desktop layers.

The repository's Koronos kernel is currently an **architecture-neutral host runtime**, not a freestanding Linux-replacement kernel. The startup integration therefore starts `chimera_kernel` under systemd and exposes Aurora as a normal Wayland session. A future bare-metal Koronos image can reuse the same ABI and service/session contracts without pretending that the present host runtime is already bootable firmware.

## Boot sequence

```text
UEFI/BIOS
   |
   v
Existing Linux bootloader + Linux kernel
   |
   v
systemd
   |
   +--> chimera-kernel.service
   |       |
   |       +--> /usr/bin/chimera-kernel
   |       +--> /run/chimera/kernel.ready
   |
   v
Display manager / logind
   |
   v
Aurora (Chimera II) Wayland session
   |
   +--> aurora-session
           |
           +--> native aurora-compositor (when installed)
           +--> sway
           +--> weston
           +--> labwc
           +--> kwin_wayland
```

## Build

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON -DCHIMERA_BUILD_STARTUP_RUNTIME=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
sudo cmake --install build
```

## Enable kernel startup

After installation:

```bash
sudo chimera-enable-startup
systemctl status chimera-kernel.service
cat /run/chimera/kernel.ready
```

The kernel runtime is deliberately non-destructive and does not alter disks, firmware, bootloader configuration, or drivers.

## Enable Aurora

The installer places `aurora.desktop` in the standard Wayland-session directory. Select **Aurora (Chimera II)** in the installed display manager. For automatic login, use the display manager's native autologin configuration and select the Aurora session.

For embedded or lab deployments where a system service is preferred:

```bash
sudo systemctl enable --now aurora-session@<username>.service
```

This mode is intentionally optional because display managers provide the correct logind/seat, DRM device access, PAM, environment, and session lifecycle for normal workstation use.

## Compositor selection

`/usr/lib/chimera/aurora-session` checks, in order:

1. `AURORA_COMPOSITOR` if explicitly configured.
2. `aurora-compositor` if a native compositor is installed.
3. `sway`.
4. `weston`.
5. `labwc`.
6. `kwin_wayland`.

This fallback is a compatibility bridge; it does not rebrand those projects as Aurora.

## Failure behavior

- If the kernel runtime cannot create `/run/chimera/kernel.ready`, startup fails without modifying persistent storage.
- If no Wayland compositor is available, the Aurora session exits with a diagnostic instead of starting an unsafe graphical process.
- systemd restarts the kernel runtime after an unexpected failure.
- The readiness marker is removed during normal shutdown.

## Future bare-metal stage

A genuine standalone Chimera II boot image still requires, at minimum:

- UEFI/Multiboot2 entry protocol and boot information ABI.
- Freestanding allocator and physical/virtual memory initialization.
- Interrupt descriptor tables and timer/APIC setup.
- SMP bring-up and scheduler context switching.
- PCIe, storage, USB and GPU driver layers.
- DRM/KMS-compatible display backend or an explicitly defined native display protocol.
- Wayland compositor and client runtime built for the Chimera userspace ABI.

Those components are not silently substituted by the host runtime. The separation keeps the current research build truthful, testable, and backward-compatible.
