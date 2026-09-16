# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate hosted/bare-metal computer and mobile editions.

## Editions

- **Hosted Edition** — runs on Windows, Linux/Unix, macOS, Android or iOS/iPadOS as an application/runtime environment.
- **BareMetal Edition** — boots directly on a validated computer/mobile hardware profile through BIOS/MBR, UEFI or a platform-specific mobile boot path.

## Universal boot and startup

The boot layer now has a normalized `CHMBOOT1` contract in `boot/boot_protocol.json`. Chimera can be entered through its native loader or a compatible/chainloaded loader instead of requiring one boot manager. Computer boot targets include BIOS/MBR, UEFI, Multiboot1/2, Limine-compatible handoff and chainloading. Limine documents BIOS and UEFI entry protocols and configuration options, while UEFI uses EFI applications and BIOS legacy boot begins in real mode. citeturn0search0turn0search7turn0search11

On x86/x86-64, `boot/mode_matrix.json` and `boot/x86/entry/mode_switch.S` define the real16 -> protected32 -> long64 transition boundary. AMD documents real, protected and long mode in AMD64; Intel documents real-address and protected operation in IA-32/Intel 64. citeturn0search96turn0search97 Other architectures use their native privilege/exception levels rather than pretending they have x86 real mode.

Startup is **menu first, GUI second**. Jasper/Spit Fire exposes normal, safe graphics, diagnostics, recovery and native-chainload choices. After handoff, the Aurora boot UI reports firmware, bootloader, hardware, memory, graphics, Koronos, drivers, networking, system services, Aurora and user-session phases. `boot/startup/boot_phase_manifest.json` is the machine-readable phase/application list.

The boot visual is represented by `boot/splash/aurora_boot_splash.svg`, a 3840x2160 Aurora Wayland Glass artwork, with a freestanding boot UI contract in `boot/splash/aurora_boot_ui.h`. The Library already contains the approved Aurora Wayland Glass reference artwork, including the glass UI, scenic high-resolution background, launcher and system widgets. fileciteturn80file1L18-L40

## Universal ISA, operands and binary encodings

The ISA layer is split into a family index and canonical instruction database:

- `isa/world_architectures.json` — RISC, CISC, EPIC and Chimera-native families.
- `isa/isa_database.json` — normalized instructions with operands, syntax, width, binary value and fixed-bit mask.
- `isa/isa_database.sql` — SQLite schema.
- `tools/validate_isa_registry.py`, `tools/load_isa_database.py`, `tools/isa_registry_report.py` — validation, loading and coverage.

## Boot/build files

- `boot/boot_protocol.json` — firmware/bootloader/kernel handoff contract.
- `boot/mode_matrix.json` — architectural execution-mode registry.
- `boot/x86/entry/mode_switch.S` — x86 mode-transition boundary.
- `boot/uefi/ChimeraLoader.c` — UEFI loader entry boundary.
- `boot/startup/boot_phase_manifest.json` — GUI startup phases and applications.
- `boot/splash/aurora_boot_splash.svg` — embedded-style Aurora boot artwork.
- `tools/build/build-hosted.bat`, `.ps1`, `.sh` — hosted builds.
- `tools/build/build-msi.ps1` + `packaging/windows/ChimeraIIOS.wxs` — Windows MSI pipeline.
- `tools/build/build-mobile.sh` — mobile hosted orchestration.
- `tools/build/build-baremetal.sh`, `.ps1` — bare-metal builds.
- `tools/build/build-all.sh` — aggregate build orchestration.

## Mobile editions

Android has hosted APK/AAB and device-profiled bare-metal editions. iOS/iPadOS has a hosted Swift/Objective-C/C++ edition and research-only bare-metal targets where a lawful and technically available boot path exists. The mobile device matrix and MHAL remain the authoritative hardware qualification layer.

## Security and provenance

Downloaded code, drivers, firmware, ROMs and applications are not automatically trusted. Secure Boot, Android AVB, vendor boot protections and Apple secure boot are respected. Bare-metal build automation does not silently flash hardware; target selection, compatibility validation, signature verification and recovery/rollback remain explicit.
