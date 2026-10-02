# Chimera II OS — Runtime and Mobile Gap Register

This register is an implementation checklist, not a claim that every item is already complete.

## Aurora Desktop / Live CD

- [x] Real Wayland compositor session through labwc/wlroots.
- [x] D-Bus user session and logind-compatible tty1 handoff.
- [x] Waybar, wallpaper, notifications, PipeWire/WirePlumber and XWayland startup.
- [x] Offline repository artwork catalog and hardcoded SVG/PNG fallbacks.
- [x] Unified text/GUI progress monitor for installation, Live CD, recovery, first boot and mobile flashing.
- [ ] GPU capability-specific effects profile: software, llvmpipe, Mesa accelerated, vendor accelerated.
- [ ] Per-output HiDPI profiles and dynamic monitor hotplug policy.
- [ ] Full accessibility service: screen reader, magnifier, high contrast, keyboard navigation and on-screen keyboard.
- [ ] Desktop settings daemon with atomic configuration transactions.
- [ ] Crash recovery for compositor/panel/session clients without forcing a full reboot.
- [ ] Suspend/resume validation matrix for VMware, QEMU, Intel, AMD and ARM64 platforms.

## Installer / Live CD

- [x] Static boot-menu progress messages.
- [x] Runtime progress state consumed by Aurora text/GUI monitor.
- [ ] Replace placeholder installation.img fallback with a validated installer image in every release profile.
- [ ] Real-time per-file/per-block write progress from the storage backend.
- [ ] Transaction journal with resumable installation after power loss.
- [ ] Preflight verification of EFI System Partition, filesystem, boot entries and free space.
- [ ] Atomic bootloader installation with rollback if verification fails.
- [ ] Final reboot gate that verifies the installed boot target before rebooting.

## Koronos / microkernel

- [ ] Hardware discovery result must become a persistent driver-selection contract before userspace starts.
- [ ] Device hotplug event bus with stable device IDs.
- [ ] IOMMU/DMA policy enforcement for every DMA-capable device.
- [ ] Per-driver isolation and restart policy.
- [ ] Unified interrupt routing diagnostics for x86_64 and ARM64.
- [ ] Timekeeping abstraction with invariant TSC/HPET/ARM counter validation.
- [ ] SMP bring-up and CPU-offline/online lifecycle tests.
- [ ] Scheduler latency and IPC microbenchmarks exposed to the diagnostics UI.
- [ ] Kernel panic/crash dump persistence and safe reboot path.
- [ ] TPM measured-boot event log integration.

## Security / Boot

- [ ] Signed kernel/initramfs/artifact manifest and verification before handoff.
- [ ] Secure Boot key enrollment workflow without bypassing platform security.
- [ ] Measured boot into TPM PCRs and a user-visible verification state.
- [ ] Anti-rollback metadata for production update channels.
- [ ] Recovery image version compatibility check before mounting or switching roots.

## Mobile edition

- [ ] Device abstraction layer for ARM64 SoC families.
- [ ] Display/touch/input pipeline with rotation and multi-touch.
- [ ] GPU/DRM backend and hardware composer policy.
- [ ] Audio codec, microphone, speaker, headset and Bluetooth audio policy.
- [ ] Wi-Fi, Bluetooth, modem and SIM/eSIM abstraction.
- [ ] Camera sensor/ISP abstraction with privacy indicator.
- [ ] USB-C host/device/PD role management.
- [ ] Battery fuel-gauge, charging, thermal and suspend policy.
- [ ] Sensors: accelerometer, gyroscope, magnetometer, proximity, ambient light.
- [ ] A/B system update slots, boot-success marking and automatic fallback.
- [ ] Recovery/fastboot-like maintenance mode with signed artifacts.
- [ ] OTA download, verification, staged install and rollback.
- [ ] Mobile-specific Aurora shell: touch-first launcher, notifications, quick settings, lock screen and gesture navigation.
- [ ] Screen scaling and safe-area policy for notches/cutouts.
- [ ] Offline factory-reset and encrypted-user-data recovery workflow.

## Update model

For mobile production updates, use a verified update chain rather than replacing a live system in place. Android's documented A/B flow is a useful interoperability reference: an updated slot is only marked successful after a successful boot, with rollback protection considered separately. citeturn0search6

## Architecture principle

Keep the low-level system native-first, but expose stable POSIX/NT/Darwin compatibility layers above the kernel. Keep desktop policy in userspace and keep mobile hardware support behind explicit HAL-style interfaces so the same Koronos core can serve desktop, server, emulator and mobile profiles.
