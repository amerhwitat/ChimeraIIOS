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
| Java | Koronos semantic/JVM interoperability | `src/java/` |
| Node.js | Web/integration runtime | `src/node/` |
| Python | Reference research, ML/RL and data-processing layer | `src/python/` |

The .NET tracks target `net8.0`, `net9.0` and `net10.0`. Native boot-critical code remains independent of the managed runtime.

## Unified ISO and Application Center

The ISO pipeline now bundles the application catalog, provider metadata, application-manager source, mobile device profiles and ecosystem documentation alongside the bootable bootstrap image. Open-source/core components can be bundled directly. Proprietary applications such as YouTube, Discord, Telegram and Microsoft software are represented through official web/store/distribution adapters instead of unauthorized binary redistribution.

Supported provider classes include native Chimera packages, Linux repositories, Flatpak, AppImage, Windows MSIX/AppX and EXE/MSI, Android APK/AAB metadata and web/PWA applications. Apple integration is intentionally a catalog/distribution adapter rather than a claim that arbitrary iOS App Store binaries can be installed on non-Apple hardware.

Run the catalog locally with:

```bash
python3 appcenter/cli/chimera-appctl.py list
python3 appcenter/cli/chimera-appctl.py install-plan youtube
```

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
  +-- APP CENTER: native / Linux / Flatpak / AppImage / Windows / Android / Web
  +-- KORONOS MOBILE: AArch64 / GKI-KMI / vendor modules / AVB
  |
  +-- LANGUAGE BRIDGES: C/C++ <-> MSVC <-> C#/.NET <-> Java <-> Node.js <-> Python
```

The 8192-bit processor is an architectural/emulation research target, not a claim of existing 8192-bit silicon. Physical performance and energy claims require measured implementations.

## Bootable ISO

`boot/iso/` contains a reproducible GRUB2/Multiboot2 bootstrap ISO pipeline. The GitHub Actions workflow builds `chimera2os-bootstrap.iso`, validates the application/mobile metadata and publishes the ISO plus SHA-256 checksum as an artifact. The current image remains a bootstrap kernel image; full Koronos drivers/services are integrated incrementally rather than being falsely represented as bare-metal complete.

## Windows setup

`installer/windows/` contains the native bootstrap/host detection boundary. Modern .NET support follows Microsoft's OS/version matrix. Windows 7/8.1 are not claimed to support .NET 8+; legacy hosts require a separate native compatibility package if supported. The installer is an in-place host integration/setup layer, not an unsupported replacement for Windows Setup.

## Crypto/AI integration

`docs/CRYPTO_AI_SCANNER_INTEGRATION.md` defines public blockchain observation, normalized storage, AI/RL workloads and deterministic C8192/R8192 vectors. Wallet operations require operator-controlled wallets or externally signed transactions. Private-key cracking, address-targeted brute force, seed guessing and unauthorized credential access are excluded.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/installer/test_installer_plan.py
python3 appcenter/cli/chimera-appctl.py list

dotnet build src/csharp/ChimeraIIOS.Managed/ChimeraIIOS.Managed.csproj
cd boot/iso && ./build-iso.sh
```

## Documentation

See `docs/APPLICATION_ECOSYSTEM.md`, `docs/MOBILE_PORTING_MATRIX.md`, `docs/LEGAL_AND_PROVENANCE.md`, `docs/INSTALLATION_AND_BOOT.md`, `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`, `docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md`, `boot/iso/README.md`, `installer/windows/README.md` and the language-specific READMEs.
