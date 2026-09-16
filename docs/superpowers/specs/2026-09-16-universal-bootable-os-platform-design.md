# Chimera II OS Universal Bootable Platform — Design Specification

**Date:** 2026-09-16  
**Status:** Design approved in chat; implementation gated on written-spec review  
**Repository:** `amerhwitat/ChimeraIIOS`

## 1. Purpose

Turn Chimera II OS from a research/build repository into a reproducible, downloadable, bootable platform distribution while preserving its existing Koronos, Spit Fire, Jasper, Aurora, Nucleus, Hive, Kore, Aegis, Spotnik and CEF architecture.

The deliverable is a source-first operating-system distribution with:

- a bootable x86-64 ISO as the first production target;
- BIOS/MBR legacy entry and UEFI/GPT entry paths;
- El Torito optical-media boot semantics;
- a Spit Fire boot boundary and Koronos kernel handoff;
- Live, Install, Recovery, Diagnostics and Safe Graphics modes;
- a hardware-aware installer with explicit disk/network actions;
- `/src` containing source needed for the distribution and `/opt` for optional applications/utilities;
- Aurora Gates desktop/application selection;
- application integration metadata for `amerhwitat/nlp`, BizX, BizXtreme, games, networking, Thamudic and utilities;
- driver, filesystem, binary-format, package-format and command-reference registries;
- compatibility/runtime adapters for supported foreign ecosystems;
- mobile edition build/packaging paths;
- reproducible CI artifacts, checksums, provenance metadata and GitHub Releases.

The system must never silently erase disks, bypass firmware security, flash devices, install proprietary components without redistribution rights, or execute arbitrary Internet content as trusted code.

## 2. Current Baseline

The repository already contains a normalized `CHMBOOT1` boot contract, x86 mode-transition boundary, UEFI loader boundary, startup manifest, ISO tooling, edition build workflows, application metadata, mobile device profiles, driver acquisition workflow and security/provenance controls. The current ISO workflow produces a structured ISO artifact when its CI dependencies and existing bootstrap sources succeed, but a public GitHub Release and verified downloadable release artifact are not assumed until CI has actually completed successfully.

The existing ISO builder currently uses a 32-bit Multiboot2 bootstrap and `grub-mkrescue`/xorriso authoring. This design retains that bootstrap where useful, but adds explicit BIOS/UEFI media validation, release manifests and a production-oriented handoff path rather than claiming that a staging tree alone proves every firmware path works.

## 3. Architecture

### 3.1 Boot layers

The boot stack is layered as:

`Firmware -> media discovery -> Spit Fire -> Jasper/menu -> CHMBOOT1 -> Koronos -> hardware/driver discovery -> services -> Aurora/session`

BIOS and UEFI are treated as different firmware interfaces. BIOS legacy services/interrupts are exposed only through the legacy compatibility boundary; UEFI is entered through EFI applications, protocols and boot/runtime services. The design does not incorrectly model modern UEFI as a collection of BIOS interrupts.

Supported computer entry families:

- BIOS/MBR legacy boot;
- UEFI on GPT media;
- UEFI removable-media fallback through the standard EFI boot path;
- El Torito optical boot;
- Multiboot1/Multiboot2 handoff;
- Limine-compatible handoff where the compatibility contract is satisfied;
- controlled chainloading of an existing native bootloader.

x86-64 transitions remain `real16 -> protected32 -> long64` where a legacy firmware path requires it. ARM64 and RISC-V64 use native architectural entry/exception levels rather than emulated x86 modes.

### 3.2 Media layout

The ISO staging tree will be organized approximately as:

```text
/
├── EFI/BOOT/                 # UEFI loader and architecture-specific boot assets
├── boot/                     # Spit Fire, Jasper, kernel/initrd, boot configs
├── src/                      # distribution source tree
│   ├── Koronos/
│   ├── SpitFire/
│   ├── Aurora/
│   ├── Nucleus/
│   ├── Hive/
│   ├── Kore/
│   ├── Aegis/
│   ├── Spotnik/
│   ├── CEF/
│   └── applications/
├── opt/                      # optional applications/utilities and integration payloads
├── install/                  # installer, partitioning, network and upgrade tooling
├── packages/                 # package indexes/cache metadata; licensed payloads only
├── drivers/                  # hardware/driver metadata and permitted redistributables
├── filesystems/              # filesystem adapters, probes and metadata
├── repositories/             # repository/package-source definitions
├── man/                      # original/generated command references and licensed man sources
├── games/
├── wallets/
├── ISO/                      # media manifests and build metadata
└── docs/
```

The final ISO will use ISO-9660 with appropriate optical extensions. Rock Ridge/Joliet/UDF support is represented by the media/build registry and validated according to the selected authoring backend; the runtime filesystem layer remains independent from the ISO authoring format.

### 3.3 Boot modes and Gates Menu

The first visible interface is a text/graphics-capable startup menu. It includes:

1. Chimera II OS — Live
2. Chimera II OS — Install
3. Safe Graphics
4. Diagnostics
5. Recovery
6. Network Install/Recovery
7. Chainload Native Bootloader

After successful kernel/service initialization, Aurora presents the **Gates Menu** for selecting an installed/available desktop environment or personality and launching applications, games, networking, crypto/wallet tools, Thamudic and NLP tools, system administration and recovery utilities.

### 3.4 Installer

The installer is a staged transaction:

`detect -> explain -> select target -> partition plan -> filesystem plan -> network plan -> package/driver plan -> dry-run -> explicit confirmation -> write -> verify -> boot-entry registration -> reboot`

Disk operations are never implicit. Supported modes include:

- use free space;
- install beside an existing supported OS where a safe partition layout can be established;
- use a selected disk after explicit confirmation;
- manual partitioning;
- recovery/repair without installation.

The installer detects firmware mode, architecture, CPU, memory, storage, graphics, network devices, Secure Boot state, existing OS evidence and supported filesystem metadata. It supports IPv4 and IPv6 configuration, including DHCP/SLAAC where available and manual static configuration.

Windows/Linux/macOS migration and upgrade are implemented as discovery/import/migration workflows. They do not promise replacement of protected vendor recovery systems or proprietary firmware, and they do not overwrite an existing installation without explicit confirmation.

### 3.5 Filesystems and file security

The filesystem registry covers read/probe/install capability separately, rather than claiming every filesystem is writable everywhere. Initial registry targets include FAT12/16/32, exFAT, NTFS, ext2/3/4, XFS, Btrfs, ZFS, ISO-9660, Rock Ridge, Joliet, UDF, SquashFS, tmpfs, proc/sysfs and network filesystem adapters.

The file-security layer normalizes, where the underlying filesystem permits it:

- POSIX permissions and ownership;
- chmod/chown/chgrp;
- ACL operations and setfacl/getfacl;
- extended attributes and immutable/attribute operations where supported;
- SELinux labels/policy integration where supported;
- NTFS ACL/SID metadata mapping;
- macOS-compatible xattrs/security metadata where technically available;
- Windows attributes and ACL tooling through the compatibility layer.

The GUI file manager exposes create, rename, append/edit, delete, copy/move, properties, permissions/security, keyboard navigation, mouse selection, double-click activation and context/right-click menus through a shared UI contract.

### 3.6 Drivers and hardware database

A driver registry identifies hardware using PCI, USB, ACPI, DMI and platform-specific identifiers. Each record includes vendor/device identifiers, supported architectures, driver implementation, source URL, binary URL where lawful, version, license, checksum/signature status, provenance, compatibility status and installation method.

Driver acquisition is advisory and provenance-aware. Native Chimera drivers take priority. Linux/Unix/Windows/macOS implementations can be imported as source, metadata or compatibility references when their licenses and technical interfaces permit it. Proprietary binaries are not copied into the public distribution merely because they are discoverable online.

### 3.7 Binary and package compatibility

The binary registry distinguishes:

- ELF;
- PE/COFF and PE32+ EFI images;
- Mach-O;
- WebAssembly;
- Java class/JAR;
- .NET assemblies;
- scripts.

Package adapters cover common ecosystems such as `deb/dpkg`, `rpm/dnf/yum`, `zypper`, `pacman`, `apk`, `xbps`, `emerge`, BSD `pkg`/`pkg_add`, Homebrew, Python/pip, npm, Cargo, NuGet/.NET and archive formats. An adapter may parse, import, convert or delegate to a compatibility runtime; it does not imply that every foreign package is natively executable.

.NET, PowerShell, Python, Perl, POSIX shell, Bash, Windows batch/CMD and supported Java/Kotlin/Node/WebAssembly toolchains are represented in the toolchain registry with version/provenance metadata.

### 3.8 Applications

Application integration is manifest-driven. The platform will build or package supported source from:

- `amerhwitat/nlp`;
- `amerhwitat/BizX`;
- `amerhwitat/BizXtreme`;
- `amerhwitat/general`;
- Chimera II OS native applications;
- Thamudic/North Arabian tools;
- games, networking tools and utilities.

The source remains in `/src/applications` when it is part of the core distribution; optional runnable applications are staged under `/opt`. Each application declares language, build system, dependencies, license, supported editions and launcher metadata.

The Aurora panel system exposes applications by category instead of hard-coding repository-specific paths.

### 3.9 Command and documentation layer

A unified command-reference system provides original concise cheat sheets and references to upstream man-page repositories/licensed source. It covers POSIX/Linux CLI, Windows CMD/batch, PowerShell, filesystem operations, networking, Git and package managers.

The project will not bulk-copy arbitrary copyrighted Internet cheat sheets or man pages. Upstream licenses and attribution are recorded in `repositories/` and `docs/licenses/` when source text is redistributed.

### 3.10 Web, development and mobile layers

The distribution includes manifests/build targets for Python, Java, Node.js, Kotlin, WebAssembly, three.js and Next.js/Web UI applications where source exists and dependencies are legally redistributable or fetched during a reproducible build.

Mobile editions remain separate from the computer microkernel implementation. Android supports hosted APK/AAB and qualified device profiles. iOS/iPadOS supports hosted Swift/Objective-C/C++ application packaging where permitted. Flashing tools are explicit, device-profile constrained and confirmation-gated.

## 4. Data flow and provenance

Every imported artifact follows:

`discover -> identify -> license check -> source/binary provenance -> checksum/signature -> compatibility check -> sandbox build/test -> registry -> optional staging`

Build outputs receive SHA-256 hashes and machine-readable manifests. Release metadata records source revision, toolchain versions, host image, build timestamp, artifact hashes and dependency provenance.

No release artifact is described as reproducible or boot-tested unless CI records the corresponding evidence.

## 5. Build and release pipeline

CI is divided into:

1. source validation;
2. native build/test matrix;
3. ISO staging;
4. BIOS/UEFI media validation;
5. QEMU smoke tests where practical;
6. ISO checksum/SBOM/provenance generation;
7. application/mobile packaging jobs;
8. artifact upload;
9. release publication only after required jobs succeed.

Release artifacts will include, when successfully produced:

- x86-64 bootable ISO;
- ISO SHA-256 and manifest/signature metadata;
- source archive;
- architecture-specific images where a validated builder exists;
- hosted/mobile packages produced by their respective CI jobs;
- driver/package/filesystem/binary registries;
- build provenance/SBOM.

The public download page points to the GitHub Release assets, not to an unverified local path.

## 6. Error handling and recovery

Boot failures identify the failed phase and offer diagnostics/recovery. Installer failures roll back only changes performed by the current transaction when rollback is technically possible. Network/package failures leave the target untouched when possible. Driver incompatibility disables the driver and falls back to a safe device path rather than forcing installation.

Secure Boot, Android Verified Boot, Apple platform protections and vendor recovery/security mechanisms are respected. Unsupported secure-boot signing is reported as a qualification issue rather than bypassed.

## 7. Testing strategy

### Unit/contract tests

- CHMBOOT1 serialization and validation;
- boot menu state machine;
- partition-plan validation;
- IPv4/IPv6 configuration validation;
- filesystem capability registry;
- driver provenance/license schema;
- binary/package registry schema;
- Gates Menu/application manifest loading;
- file-operation and security-command contracts.

### Integration tests

- ISO staging completeness;
- BIOS El Torito structures;
- UEFI ESP structure and fallback loader presence;
- Multiboot2 header validation;
- x86 mode-transition assembly;
- Koronos handoff;
- QEMU BIOS and UEFI boot smoke tests;
- installer dry-run tests;
- network configuration parser tests;
- application manifest/build checks;
- release manifest/hash verification.

### Hardware qualification

Real hardware validation is represented separately from CI emulation. A passing QEMU test does not become a claim of universal hardware compatibility.

## 8. Scope boundaries

The implementation will not:

- copy proprietary Windows/macOS drivers or binaries into the public ISO without redistribution rights;
- copy unrestricted collections of third-party copyrighted man pages/cheat sheets;
- bypass Secure Boot/AVB/vendor boot restrictions;
- silently repartition, erase or flash a device;
- claim every listed filesystem is fully writable if only probing/reading is implemented;
- claim every application from every linked repository builds on every architecture;
- publish a GitHub Release until its artifacts are actually generated and verified.

## 9. Phased implementation order

**Phase 1 — Specification and release foundation:** this design, registry schemas, media manifest, release metadata and CI contract.

**Phase 2 — Bootable ISO:** Spit Fire/Jasper integration, BIOS/MBR, UEFI/GPT, El Torito, Live/Install/Recovery/Diagnostics/Safe Graphics, source/optional-app staging.

**Phase 3 — Installer:** hardware detection, partitioning transaction model, IPv4/IPv6 setup, filesystem selection and migration/upgrade discovery.

**Phase 4 — System integration:** drivers, filesystems, binary/package compatibility, security and command-reference layers.

**Phase 5 — Aurora/application integration:** Gates Menu, NLP, BizX/BizXtreme/general, games, crypto/networking/Thamudic and browser/development tooling.

**Phase 6 — Mobile:** Android and iOS/iPadOS hosted packages, device profiles and explicit flashing/recovery helpers.

**Phase 7 — Release:** full CI matrix, ISO/QEMU validation, checksums/provenance, GitHub Release assets and public download documentation.

## 10. Acceptance criteria

The project is considered release-ready only when all required CI jobs pass and provide evidence for the corresponding claims. At minimum:

- source is public in the Chimera II OS repository;
- ISO builder completes without placeholder artifacts;
- ISO contains `/src`, `/opt`, boot configuration, kernel payload and manifests;
- BIOS/El Torito and UEFI media structures validate;
- QEMU smoke tests demonstrate the supported x86 boot paths where the test environment permits;
- installer dry-run and destructive-operation confirmation tests pass;
- ISO and release artifacts have checksums and provenance metadata;
- a GitHub Release exists with links to the actually generated artifacts;
- README download instructions point to that verified release;
- limitations are documented rather than implied away.

## 11. Support text

The requested boot-screen footer is included verbatim in the boot splash/startup metadata:

```text
created by Amer Abdullah Suleiman Hwitat
- عامر الحويطات -
Amman 11814/Jordan
for support contact amer.hwitat@proton.me
```
