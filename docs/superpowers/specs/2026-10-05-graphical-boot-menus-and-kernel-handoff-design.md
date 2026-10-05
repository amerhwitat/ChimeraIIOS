# Graphical boot menus and Koronos artifact handoff

Status: proposed design for review  
Repository: `amerhwitat/ChimeraIIOS`  
Target base: `main`

## Goal

Make every interactive boot, install, recovery, and emulator selection menu graphical, and make the UEFI loader and Koronos kernel artifacts discoverable through a validated firmware-to-kernel handoff.

## Current repository state

- `boot/boot-menu-contract.json` defines the shared menu IDs and policy.
- `boot/iso/grub.cfg`, Jasper configs, installation config, and Spit Fire configs use GRUB `menuentry` commands with `gfxterm`, but still present a traditional text list and text `echo` progress/errors.
- `boot/iso/grub-theme.txt` names artwork paths but is not itself a complete GRUB theme definition.
- `boot/jasper/jasper_main.cpp` writes a small fixed handoff record and halts; `boot/spitfire/sfu_uefi.c` prints to the firmware console and returns. The ISO build delegates the active UEFI path to GRUB's `BOOTX64.EFI` where available.
- The kernel is staged as `/boot/koronos/koronos.elf` and loaded by GRUB's `multiboot2` commands. `boot/include/chimera/bootinfo.h` already defines a handoff structure with an EFI system table pointer, framebuffer data, initrd fields, and a memory map, but the contract does not yet identify the boot artifacts/modules consistently.
- The root `build-chimera-iso.sh` makes `BOOTX64.EFI` verification optional; `boot/iso/validate-iso.py` does not require the loader file or kernel handoff manifest.

## Graphical menu behavior

- Inventory user-facing menu surfaces in the boot contract/configs, installer/recovery UI, Aurora shell/context menus, settings panels, and Aurora Emulators panel. Extend `boot/boot-menu-contract.json` so boot choices use one stable ID, label, destination, and UI accessibility descriptor; bind related menu actions to the existing Aurora GUI menu infrastructure.
- Replace text-entry-only menus and on-screen `echo` progress/errors with a full-screen graphical menu using a real GRUB theme or the existing framebuffer renderer, shared Aurora artwork, visible focus/selection, and consistent icons/status.
- Use firmware GOP on UEFI and the existing supported framebuffer/video path on BIOS. Keep early-boot UI small and independent of the full Aurora compositor.
- Support keyboard navigation, high contrast, scalable text, and RTL labels. Add pointer/touch input only where the firmware/input stack reports it.
- Do not leave an interactive text-mode menu as a fallback. If no usable graphical framebuffer exists, take the configured default/recovery action and send diagnostics to serial/logs; never wait forever for invisible menu input.
- Apply the same graphical menu contract to the Aurora Emulators panel and installer/recovery choices. Runtime preferences and panel styling remain in Aurora; early boot uses only the minimal renderer.
- Keep command-line help, logs, and serial diagnostics textual; they are not interactive menus. No user-facing menu should require text-mode selection.

## UEFI and ELF artifact handoff

- Stage and validate the UEFI application at `/EFI/BOOT/BOOTX64.EFI` for x86_64 UEFI media and the kernel at `/boot/koronos/koronos.elf`. `BOOTX64.EFI` is the firmware-launched loader; it is not the Koronos kernel image.
- Generate a boot-artifact manifest containing artifact IDs, ISO paths, sizes, SHA-256 hashes, loader format/architecture, kernel ELF format/architecture, boot protocol, and required initrd/module paths. Include it in the ISO and pass its module metadata to Koronos.
- Keep the kernel ELF and required initrd/modules readable to the loader and kernel via boot-info module entries. Extend the existing `chm_bootinfo_t` / `koronos_boot_context` contract rather than adding a parallel handoff format. The handoff must identify loader kind/version, kernel physical load bounds, module names/ranges, EFI system-table or memory-map data when valid, and framebuffer base/pitch/size/format when available.
- Validate the handoff checksum, version, pointer ranges, module bounds, and framebuffer bounds before Koronos uses them. Copy the information the kernel needs before reclaiming bootloader-owned memory or ending firmware services.
- The kernel does not execute `BOOTX64.EFI` or trust file paths supplied without validation. The EFI loader is available in the ISO and represented by verified manifest metadata; Koronos runs from the ELF image loaded by the selected bootloader.
- Require the ISO builder to fail when the expected UEFI loader or kernel ELF is absent or mismatched. Retain a separately identified BIOS path where supported and report which path was validated.

## Acceptance criteria

- ISO validation requires `/EFI/BOOT/BOOTX64.EFI`, `/boot/koronos/koronos.elf`, the boot-artifact manifest, and all manifest-listed files with matching SHA-256/size.
- QEMU UEFI and BIOS boot tests reach Koronos through the declared path. Kernel diagnostics report a valid boot context, kernel ELF bounds, initrd/module names and bounds, and framebuffer metadata where available.
- Corrupt/missing loader, ELF, module, manifest, checksum, unsupported handoff version, invalid pointer, or framebuffer bounds fail safely before memory use and select the configured recovery/diagnostic route.
- Every menu ID from the boot contract renders graphically and routes to its configured action. The primary and recovery paths contain no text-only interactive menu or text progress screen.
- The menu inventory covers every configured user-facing boot, installer, recovery, system, and Aurora emulation menu; each entry has a GUI binding and keyboard-accessible focus/navigation.
- Tests exercise keyboard-only navigation, high-contrast/large-text mode, RTL label layout, and no-framebuffer behavior (automatic default/recovery with serial diagnostics, no blocking text menu).
- The Aurora Emulators panel and installer/recovery menu entry points use the same menu IDs and state labels without pulling the full compositor into early boot.
- `build-chimera-iso.sh`, `boot/iso/build-iso.sh`, and `boot/iso/validate-iso.py` report the UEFI and BIOS path checks separately and produce a manifest matching the staged ISO contents.

## Out of scope

- Loading or executing the EFI application from inside Koronos after handoff.
- Making unavailable firmware framebuffer or pointer hardware appear supported.
- Replacing the measured-boot trust policy or weakening boot-artifact verification.
- A full Aurora compositor in firmware/bootloader mode.

