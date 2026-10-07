# Chimera II OS / Aurora 2026 Enhancement Research

Date: 2026-10-07

This document records practical enhancements selected from current upstream Linux,
Wayland, desktop, virtualization, security and emulation work. The goal is to
adopt standards and capabilities rather than copy proprietary implementations.

## Priority 0 — Boot integrity and recovery

### Sealed UKI + fs-verity / composefs profile

Add an optional production profile based on Unified Kernel Images, Secure Boot,
composefs and fs-verity. The design should preserve the existing GRUB/Jasper/
Spit Fire fallback path for development and unsupported firmware.

Benefits:
- cryptographically bound kernel/initrd/command line;
- root filesystem integrity verification;
- safer automatic rollback;
- future TPM-backed unattended disk unlocking.

Upstream references:
- systemd recommends UKIs with systemd-boot for modern UEFI systems.
- bootc sealed images combine UKIs, Secure Boot and composefs/fs-verity.

## Priority 1 — Aurora Wayland graphics

### Color management / HDR
Track the Wayland color-management protocol and expose output/content color
profiles in Aurora. Keep HDR opt-in until compositor and GPU support is verified.

### Fractional scaling
Adopt fractional-scale-v1 for per-surface rendering so 125%, 150% and other
non-integer display scales remain sharp.

### Low-latency presentation
Expose tearing-control-v1 as an application/compositor hint for games,
drawing and latency-sensitive applications.

### VRR
Add a display profile that detects VRR capability and enables low-latency
cursor behavior without forcing VRR on unsupported displays.

## Priority 1 — Remote desktop

Build a native Aurora remote-support panel around Wayland-native RDP/VNC
capabilities with:
- GPU-accelerated streaming where available;
- HiDPI scaling;
- camera redirection;
- unattended/headless sessions;
- explicit user consent and session audit;
- portal-mediated screen/camera access.

## Priority 1 — Security sandboxing

Add Landlock profiles to Aurora application launchers. Use filesystem and
network restrictions for untrusted applications without requiring root.

Suggested profiles:
- browser: no raw device access, restricted filesystem, controlled network;
- media player: read-only media paths plus portal access;
- document viewer: read-only documents and no network by default;
- downloaded tool: isolated home/cache and explicit network policy.

Landlock network and IPC scope controls are available in current Linux
interfaces and can stack with existing access controls.

## Priority 1 — Accessibility

Add:
- reduced-motion global policy;
- screenshot OCR;
- improved screen reader/AT integration;
- virtual keyboard enhancements;
- braille integration;
- per-display scaling;
- remote accessibility/session support.

## Priority 2 — Virtualization

Create a QEMU 11 profile with:
- virtio-GPU multi-output;
- confidential VM profiles where host hardware supports them;
- snapshots;
- migration profiles;
- RISC-V/ARM/x86 capability detection;
- per-VM display resolution.

The capability registry must describe availability rather than claim every
host supports every accelerator.

## Priority 2 — Media

Use PipeWire/WirePlumber portal-mediated device permissions for:
- audio;
- Bluetooth;
- cameras;
- screen capture;
- media routing.

Add hardware-accelerated video encode/decode detection and expose the selected
backend in Aurora Settings.

## Priority 2 — Gaming and emulation

Maintain the existing MAME integration and add a modern profile for current
MAME releases, including:
- SDL controller mappings;
- per-game artwork/metadata;
- save states;
- rewind;
- runahead where the selected core supports it;
- netplay where supported;
- latency/VRR display mode.

## Priority 3 — Secure personal data

Evaluate systemd-homed-style encrypted home lifecycle integration so encrypted
home credentials can be suspended during system sleep and reacquired on
resume.

This remains optional and must not replace Chimera's existing identity
contracts until tested on the supported filesystem and login stack.

## Implementation policy

1. Prefer upstream protocols and documented interfaces.
2. Never silently enable insecure boot or bypass vendor security.
3. Capability detection must precede feature activation.
4. Every optional accelerator requires a safe fallback.
5. Remote access and device capture require explicit permissions.
6. Proprietary code is not copied into Chimera II OS.
7. Experimental protocols remain opt-in and are clearly labeled.
8. Build artifacts must remain reproducible.

## Research sources

- KDE Plasma 6.6/6.7 feature releases
- GNOME 50 release notes
- systemd boot component / UKI documentation
- bootc sealed-image and composefs documentation
- Linux Landlock documentation
- Wayland color-management, fractional-scale and tearing-control protocols
- PipeWire/WirePlumber feature and portal documentation
- QEMU 11.0/11.1 release notes
- MAME 0.289 and current MAME development requirements
