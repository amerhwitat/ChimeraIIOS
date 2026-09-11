# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop/mobile, networking, data and intelligent-computing ecosystem.**

> Status: public research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, mobile-hardware and silicon targets.

## Unified language matrix

| Language / toolchain | Role | Location |
|---|---|---|
| C / C++ | Kernel, ISA, boot, native desktop and hardware-facing implementation | `src/cpp/`, `src/kernel/`, `src/arch/` |
| Visual C++ / MSVC | Windows-native bootstrap, host integration and installer-facing code | `src/vcpp/` |
| C# | Managed Windows/cross-platform services and desktop tooling | `src/csharp/` |
| F# | Functional .NET research/runtime layer | `src/dotnet/fsharp/` |
| Visual Basic .NET | Managed Windows compatibility/tooling layer | `src/dotnet/vb/` |
| Java | Koronos semantic/JVM interoperability and application-service bridge | `src/java/` |
| Node.js | Web/integration runtime and service bridge | `src/node/` |
| Python | Reference research, ML/RL, data-processing and service bridge | `src/python/` |

## Unified ISO and Application Center

The ISO pipeline bundles the application catalog, provider metadata, application-manager source, package-source registry, mobile profiles and ecosystem documentation alongside the bootable bootstrap image. Proprietary applications are represented through official catalog/store adapters rather than unauthorized binary redistribution.

The ISO Tool integration under the companion `nlp/ISO-Tool` tree can compile/link a repository, collect generated executables and libraries, stage the complete source tree under `/src`, prepare `/applications/linux` and `/applications/windows`, export Chimera II Spit Fire boot artifacts, and master CD/DVD ISO images through configured backends.

## Structured boot and ISO architecture

`boot/spitfire/` now contains the staged SF0/SF1/SF2 BIOS implementation sources, the SFU UEFI source contract and shared boot ABI headers. `kernel/arch/x86_64/` contains the Koronos boot handoff/linker contract. `boot/iso/build-iso.sh` first creates a deterministic media tree and then masters an ISO 9660/El Torito image through GRUB2/xorriso.

The staged tree contains `/boot/spitfire`, `/boot/jasper`, `/boot/koronos`, `/EFI/BOOT`, `/EFI/CHIMERA`, `/chimera`, `/src` and `/checksums`. BIOS Multiboot2 remains the current executable bootstrap; UEFI uses the standard `EFI/BOOT/BOOTX64.EFI` path when the GRUB EFI authoring environment is available. The R8192/C8192 ISA remains explicitly experimental/virtual.

See `docs/STRUCTURED_ISO_BUILD.md` and `boot/iso/README.md` for the complete layout and verification contract.

## Unified package management

`package-manager/chimera-pkg.py` provides a common command surface while retaining native package managers:

- Debian/Ubuntu: `apt`, `apt-get`, `dpkg` and `.deb`
- Fedora/RHEL/Rocky: `dnf`, `yum`
- openSUSE: `zypper`
- Arch: `pacman`
- Alpine: `apk`
- Void: `xbps-install`
- Gentoo: `emerge`
- Homebrew: `brew`
- Flatpak: `flatpak`
- Snap: `snap`
- Windows: `winget`/Microsoft Store, Chocolatey and Scoop
- `fnd`: reserved compatibility hook for the requested Chimera command vocabulary

Repository URLs and package formats are stored in `package-manager/repositories.json`. The registry is official-first, HTTPS-only by policy, provenance-aware and explicit about third-party sources. See `docs/PACKAGE_MANAGEMENT_AND_REPOSITORIES.md`.

Examples:

```bash
python3 package-manager/chimera-pkg.py detect
python3 package-manager/chimera-pkg.py sources
python3 package-manager/chimera-pkg.py plan apt curl
python3 package-manager/chimera-pkg.py plan winget Git.Git
python3 package-manager/chimera-pkg.py install apt curl --yes
```

The adapter never executes a plan unless `--yes` is explicitly supplied.

## Mobile / Koronos Mobile

`mobile/` contains the Android-class Koronos Mobile architecture, AArch64 device-profile schema, Qualcomm/MediaTek/Samsung templates, profile validation and a reproducible research-image builder. Android's GKI/KMI and vendor-module model, AVB and rollback protection are treated as first-class constraints. Exact handset support requires model-specific validation; the project does not claim one binary boots every Samsung or Chinese-manufacturer device.

## Architecture baseline

```text
CHIMERA II OS
  |
  +-- MACHINE: R8192 / C8192 / RegisterN / Tensor / Vector
  +-- COGNITIVE: Koronos 128D / knowledge / reasoning research
  +-- WORLD: network / GPU / files / sensors / storage / UI
  |
  +-- KORONOS: ISA / MM / scheduler / IRQ / VFS / IPC / networking
  +-- SPIT FIRE + JASPER: boot and boot-manager layers
  +-- AURORA / GPU / CEF / WEB
  +-- APP CENTER + PACKAGE MANAGER: native / Linux / Flatpak / AppImage / Windows / Android / Web
  +-- KORONOS MOBILE: AArch64 / GKI-KMI / vendor modules / AVB
```

The 8192-bit processor is an architectural/emulation research target, not a claim of existing 8192-bit silicon. Physical performance and energy claims require measured implementations.

## Bootable ISO

`boot/iso/` contains the reproducible structured ISO pipeline. It stages the Spit Fire/Jasper/Koronos artifacts, application metadata, mobile profiles, documentation, toolchain registries and checksums into a deterministic tree and then creates `chimera2os-bootstrap.iso`. The existing Multiboot2 bootstrap remains the current executable kernel image; the new low-level boot sources provide the native Spit Fire implementation boundary for continued development.

## Windows setup

`installer/windows/` contains the native bootstrap/host detection boundary. Modern .NET support follows Microsoft's OS/version matrix. Windows 7/8.1 are not claimed to support .NET 8+; legacy hosts require a separate native compatibility package if supported.

## Crypto/AI integration

`docs/CRYPTO_AI_SCANNER_INTEGRATION.md` defines public blockchain observation, normalized storage, AI/RL workloads and deterministic C8192/R8192 vectors. Wallet operations require operator-controlled wallets or externally signed transactions. Private-key cracking, address-targeted brute force, seed guessing and unauthorized credential access are excluded.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/installer/test_installer_plan.py
python3 appcenter/cli/chimera-appctl.py list
python3 package-manager/chimera-pkg.py detect
python3 -m pytest -q tests/boot tests/iso

dotnet build src/csharp/ChimeraIIOS.Managed/ChimeraIIOS.Managed.csproj
cd boot/iso && ./build-iso.sh
```

## Documentation

See `docs/APPLICATION_ECOSYSTEM.md`, `docs/PACKAGE_MANAGEMENT_AND_REPOSITORIES.md`, `docs/MOBILE_PORTING_MATRIX.md`, `docs/LEGAL_AND_PROVENANCE.md`, `docs/INSTALLATION_AND_BOOT.md`, `docs/STRUCTURED_ISO_BUILD.md`, `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`, `docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md`, `docs/BIZX_NODEJS_INTEGRATION.md`, `boot/iso/README.md`, `installer/windows/README.md` and the language-specific READMEs.
