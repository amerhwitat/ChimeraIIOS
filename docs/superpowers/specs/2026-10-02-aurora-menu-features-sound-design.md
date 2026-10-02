# Aurora Menu Features and Sound System — Design Specification

Date: 2026-10-02
Status: Draft for review

## Intent

Extend Aurora Desktop and all Chimera II OS boot/install/recovery/live/mobile menus with a coherent modern interaction system: functional menu actions, visible progress/state, accessibility, keyboard/touch navigation, and optional sound effects. Preserve boot reliability, text-only operation, offline operation, and the canonical asset/link policy.

## Scope

### Menu surfaces
- Spit Fire boot menu
- Jasper boot/recovery menu
- Text installer
- GUI installer
- Live CD launcher
- Recovery terminal/recovery GUI
- Aurora Desktop application/system menus
- Power/session menus
- Driver/device and hardware diagnostics menus
- Network/storage/filesystem utilities
- Mobile edition boot/installer/recovery menus

### Common capabilities
Each menu should support, where meaningful:
- keyboard navigation and mnemonics
- mouse/touch activation where a GUI exists
- focus indication
- Back/Cancel/Retry/Continue/Help actions
- disabled-state explanation
- progress indicators for long operations
- operation status and error details
- confirmation dialogs for destructive operations
- timeout-safe operation cancellation
- Arabic/English localization and RTL layout support
- high-contrast/reduced-motion/no-sound modes
- text-mode fallback with no Wayland/audio dependencies
- deterministic exit/status codes for automation

## Aurora visual/audio system

Create a shared runtime service rather than embedding audio logic in every menu.

Suggested runtime assets:

```text
/usr/share/chimera/aurora/assets/
  init.mp4
  sound/
    startup.ogg
    shutdown.ogg
    menu-open.ogg
    menu-close.ogg
    focus.ogg
    select.ogg
    back.ogg
    cancel.ogg
    confirm.ogg
    warning.ogg
    error.ogg
    success.ogg
    progress-start.ogg
    progress-complete.ogg
    notification.ogg
    device-connect.ogg
    device-remove.ogg
    network-connect.ogg
    network-disconnect.ogg
    storage-mount.ogg
    storage-unmount.ogg
    recovery.ogg
    installer-start.ogg
    installer-complete.ogg
```

All audio is optional. Missing assets, unavailable audio devices, or disabled audio must never make a menu fail.

## Sound event contract

Menus emit semantic events instead of directly invoking a particular player:

```text
menu.open
menu.close
menu.focus
menu.select
menu.back
menu.cancel
menu.confirm
operation.start
operation.progress
operation.success
operation.warning
operation.error
notification.info
device.connect
device.remove
network.connect
network.disconnect
storage.mount
storage.unmount
recovery.enter
installer.start
installer.complete
system.startup
system.shutdown
```

Aurora's sound service maps these events to assets and applies volume, mute, accessibility, and reduced-motion/reduced-sensory policy.

## Initialization video and progress

`init.mp4` is the canonical Aurora initialization visual. It is displayed as the Aurora splash/background for GUI installation and startup. Koronos publishes real initialization phases; the installer/Aurora progress UI consumes the same state rather than inventing a second percentage.

The progress protocol must expose:

```text
phase-id
phase-name
percent
message
severity
completed
failed
cancelable
```

Example phases:

```text
CPU discovery
memory initialization
interrupt/APIC initialization
scheduler
IPC
hardware/driver discovery
storage/filesystem
network
Jasper services
Aurora Wayland startup
```

The GUI may animate progress, but the reported percentage must remain the Koronos/installer state.

## Functional menu additions

### Boot
- normal Aurora boot
- recovery
- recovery terminal
- hardware diagnostics
- safe graphics
- text-only boot
- previous boot log
- reboot/shutdown

### Installer
- install
- repair installation
- filesystem tools
- disk/partition inspection
- driver inspection
- network configuration
- log viewer
- cancel with safe rollback

### Recovery
- mount root filesystem
- mount EFI
- inspect logs
- repair bootloader
- repair initramfs
- filesystem check
- network recovery
- shell
- reboot/poweroff

### Aurora Desktop
- application launcher
- terminal launcher
- settings
- network manager
- storage manager
- system monitor
- driver/device manager
- update manager
- recovery tools
- lock/log out/suspend/restart/shutdown
- notification center
- workspace/window management

## Safety and reliability

- Boot-critical EFI/GRUB/kernel/initramfs artifacts remain real files, not runtime symlinks.
- GUI enhancements never become a boot dependency.
- Audio/video playback must have static/text fallbacks.
- Destructive actions require explicit confirmation.
- Long-running actions expose cancellation where technically safe.
- Build scripts validate all referenced runtime assets before ISO creation.
- ISO verification checks BIOS and UEFI boot paths independently.

## Build and Docker integration

`build-chimera-iso.sh` will stage the canonical Aurora assets, validate them, build the image, and—when Docker credentials are available—publish the generated image to Docker Hub. Publishing remains opt-out with `--no-push` and never stores credentials in the repository or ISO.

Expected tags:

```text
<repository>:latest
<repository>:<version>
<repository>:<git-sha>
```

## Verification requirements

Before completion:

```text
bash -n build-chimera-iso.sh
bash -n all modified shell scripts
all modified C/C++ targets compile
init.mp4 is staged and validated
all referenced sound assets are staged
missing audio falls back cleanly
text-mode menus work without Wayland/audio
GUI menu actions return expected status
Koronos progress reaches 100% or reports failure
BIOS ISO validation passes
UEFI ISO validation passes
Docker image build passes
Docker push is validated when credentials are supplied
no duplicated canonical artwork/audio assets are introduced
```

## Non-goals

- Do not make proprietary Windows/macOS components part of Chimera's runtime.
- Do not require internet access for boot, installer, recovery, or Aurora operation.
- Do not make audio/video mandatory for successful installation or boot.
