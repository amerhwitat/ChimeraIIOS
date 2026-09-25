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