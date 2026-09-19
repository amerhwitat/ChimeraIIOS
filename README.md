# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate hosted/bare-metal computer and mobile editions.

## Editions

- **Hosted Edition** — runs on Windows, Linux/Unix, macOS, Android or iOS/iPadOS as an application/runtime environment.
- **BareMetal Edition** — boots directly on a validated computer/mobile hardware profile through BIOS/MBR, UEFI or a platform-specific mobile boot path.

## Universal boot and startup

The boot layer uses a normalized `CHMBOOT1` contract in `boot/boot_protocol.json`. Computer boot targets include BIOS/MBR, UEFI, Multiboot1/2, Limine-compatible handoff and controlled chainloading. BIOS legacy services and modern UEFI protocols/services are treated as separate firmware interfaces.

On x86/x86-64, the mode-transition boundary is real16 -> protected32 -> long64. Other architectures use their native privilege/exception levels rather than pretending they have x86 real mode.

Startup is **menu first, GUI second**. Jasper/Spit Fire exposes Live, Install, Safe Graphics, Diagnostics, Recovery, Network Install/Recovery and controlled native-chainload choices. After handoff, Aurora presents the **Gates Menu** for desktop personalities, applications, games, networking, crypto/wallet tools, Thamudic, NLP, browsers, development and system administration.

The boot visual is represented by `boot/splash/aurora_boot_splash.svg`; the requested support footer is stored in `boot/splash/support_footer.txt` and staged into the ISO.

## Universal source-first ISO

The structured ISO builder stages:

- `/src` — source needed by the distribution;
- `/opt` — optional applications/utilities;
- `/install` — installer contracts and future transaction tooling;
- `/drivers` — provenance-aware driver registry;
- `/filesystems` — filesystem capability registry;
- `/packages` — package-manager compatibility registry;
- `/repositories` — source/repository metadata;
- `/man` — original/licensed command references;
- `/games` and `/wallets` — optional application categories;
- `/ISO` — media layout metadata.

The first release target is x86-64 with BIOS/MBR and UEFI/GPT qualification. El Torito optical boot and UEFI removable-media structures are authored through GRUB/xorriso. GNU documents `grub-mkrescue` as a bootable ISO authoring frontend, while xorriso supports El Torito BIOS/EFI boot structures and ISO mastering. citeturn0search0turn0search2turn0search4

## Installer and compatibility contracts

`install/installer-contract.json` defines the transaction stages for hardware detection, partition planning, filesystem planning, IPv4/IPv6 configuration, driver/package planning, explicit confirmation, verification and boot-entry registration.

The registries separately describe filesystem capabilities, drivers, binary formats and package managers. A registry entry is not a claim that every target supports every operation.

Windows/Linux/macOS migration is designed as discovery/import/migration rather than silent replacement. Secure Boot, vendor recovery, Android Verified Boot and Apple security mechanisms are not bypassed.

## Application integrations

`appcenter/catalog/external-integrations.json` defines source-first integrations for public repositories including:

- `amerhwitat/nlp`
- `amerhwitat/BizX`
- `amerhwitat/BizXtreme`
- `amerhwitat/general`

Applications are built only when their source, license, dependencies and target compatibility can be verified. Proprietary binaries and drivers are not copied merely because they are discoverable online.

## Mobile editions

Android has hosted APK/AAB and device-profiled bare-metal paths. iOS/iPadOS packaging remains separate from the computer microkernel implementation and is subject to platform security and signing requirements. Flash/recovery helpers are device-profile constrained and confirmation-gated.

## CI and releases

`.github/workflows/chimera-iso.yml` validates registries, boot assets, ISO contents, El Torito/system-area metadata and BIOS/UEFI QEMU smoke paths where firmware is available. `.github/workflows/chimera-release.yml` publishes a GitHub Release only for version tags after the ISO build and verification succeed. GitHub Actions artifacts are retained for inspection before/alongside release publication. citeturn0search3turn0search6

**There is currently no published GitHub Release until a version-tagged release workflow has successfully generated and verified the artifacts.**

## Security and provenance

Downloaded code, drivers, firmware, ROMs and applications are not automatically trusted. Secure Boot, Android AVB, vendor boot protections and Apple secure boot are respected. Bare-metal automation does not silently flash hardware or erase disks; target selection, compatibility validation, signature/hash verification and recovery/rollback remain explicit.
