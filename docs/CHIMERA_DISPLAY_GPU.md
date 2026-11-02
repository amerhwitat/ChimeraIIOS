# Chimera II OS Display and GPU Driver Architecture

## Resolution

Aurora exposes Display/Resolution from the desktop right-click menu and Settings. The runtime backend order is:

1. `kscreen-doctor` on Wayland when available.
2. `wlr-randr` on Wayland when available.
3. `xrandr` on X11.

`wlr-randr` uses the Wayland `wlr-output-management` protocol and supports standard modes and refresh rates. It is only used when the compositor advertises that protocol.

The selected mode is stored per-user at `$XDG_CONFIG_HOME/chimera/display.conf` and Aurora restores it when the session starts.

## GPU drivers

`chimera-gpu-driver-manager` refreshes configured Ubuntu APT indexes and scans PCI/DRM state. It never executes arbitrary vendor shell installers downloaded from the web.

- NVIDIA: `ubuntu-drivers` chooses Ubuntu-supported/recommended driver packages.
- AMD: kernel `amdgpu` plus Linux firmware, Mesa and AMD DRM userspace.
- Intel: kernel `i915`/`xe` plus Linux firmware, Mesa and Intel media userspace.
- Unknown hardware: generic Mesa/firmware packages are installed when available.

The package repository metadata and package signatures are the trust boundary. Secure-Boot-compatible signed packages are preferred. Kernel driver changes can require a reboot.

## Commands

    chimera-display list
    chimera-display backend
    chimera-display set eDP-1 1920x1080 60
    sudo chimera-gpu-driver-manager scan
    sudo chimera-gpu-driver-manager status
    sudo chimera-gpu-driver-manager install
    sudo chimera-gpu-driver-manager repair

Arabic aliases include `إعداد_الشاشة` and `مدير_تعريفات_الرسومات`.

Graphical applications:

- `/usr/bin/chimera-display-settings.py`
- `/usr/bin/chimera-gpu-driver-manager`
- `/usr/bin/chimera-desktop-action`

## Koronos boot framebuffer and resolution policy

The x86-64 Multiboot2 header requests an optional 800x600x32 direct-RGB framebuffer. GRUB retains the existing 800x600 SVGA boot preference and 640x480 fallback. Koronos validates the Multiboot2 framebuffer tag, pitch, dimensions, RGB component masks, pixel depth and the framebuffer's full physical range before writing pixels. If the tag is absent or unsupported, VGA text and serial/debugcon remain available.

The kernel console renders into the firmware/GRUB-provided framebuffer and retains it throughout kernel initialization. This is framebuffer use, not GPU modesetting: Koronos does not yet enumerate EDID modes or program vendor GPU registers. No kernel resolution change is performed during early initialization.

Aurora's desktop preference order is 5120x2880, 1024x768, then 640x480. Only modes actually reported by the active display backend are offered; other detected modes remain available as additional choices. The preference does not imply that a display or GPU supports 5120x2880.

### Readiness-gated transition requirement

A future kernel/display backend may replace the boot framebuffer only after the selected target's genuine readiness event:
- Live: userspace-originated init syscall acknowledgement, matching nonzero PID, root filesystem and writable /tmp checks, then verified desktop/service readiness.
- Installer: actual Installer init process, process-bound syscall/VFS readiness, and storage backend readiness.
- Recovery: actual Recovery init process and verified repair environment readiness.
- Desktop: compositor/display backend initialized and a valid output/mode list returned.

A module registration, process load plan, kernel marker, service identity, or framebuffer initialization is not a target-ready event. If the preferred mode cannot be set or verified, retain the current framebuffer and report the failure. BIOS and UEFI visual tests must capture both successful transitions and fallback behavior on the same ISO SHA.

### Current implementation boundary

The Multiboot2 RGB console is implemented and covered by host parser tests and the Koronos build. Native GPU modesetting, EDID enumeration, the target-readiness event producer, compositor handoff, BIOS/UEFI visual evidence, and actual 5120x2880 hardware validation remain outstanding. Do not infer these capabilities from the framebuffer console.

