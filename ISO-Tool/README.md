# ISO-Tool

Chimera II OS ISO/image build orchestrator with native Windows/MSVC, .NET and Python implementations.

## Deep recursive source acquisition and tree scan

The tool accepts GitHub/Git repository URLs, direct ZIP/TAR source archives, local archives, and local directories. Git sources are cloned with submodules. Archives are downloaded, SHA-256 recorded, safely extracted, and scanned. Absolute/traversal archive paths and symbolic/hard links are rejected.

The recursive scanner walks every directory and records `knowledge/repository-tree.json` with source-language, build-system, image, artifact, document and script classifications. Nested build projects are independently discovered.

## Windows toolchains

ISO-Tool scans PATH, environment variables and Visual Studio registry locations for MSVC/Link/MASM, LLVM/LLD, GNU/MinGW GCC/G++, GAS/LD, NASM/YASM, CMake/MSBuild/Make and ISO mastering backends.

NASM is preferred for the Spit Fire BIOS first stage. If no external assembler is available, the dependency-free built-in bootstrap assembler emits the known one-sector Spit Fire stage. A NASM source-build path is also integrated for hosts with the required MSVC/MinGW prerequisites.

GNU C++ is used whenever G++ is detected. When it is absent, the bootstrap planner records GCC source-build requirements rather than silently executing arbitrary installers.

## Build and application pipeline

`acquire → deep recursive scan → application discovery → dependency graph → deterministic build plan → registered recursive build adapters → toolchain selection → boot-image construction → artifact staging → bootable ISO/IMG mastering`

Registered adapters cover CMake, Make, Meson, Cargo, npm, Maven, Gradle, .NET and Autotools when available. AI/RNN/LLM planning remains advisory; deterministic build/dependency rules remain authoritative.

Application discovery reports required/recommended/optional entries from Python, Node.js, Rust, Java, .NET, Go, CMake and Make manifests. Available package managers include APT, DNF, Zypper, pacman, apk, XBPS, Portage, Homebrew, Flatpak, Snap, WinGet, Chocolatey and Scoop.

Package installation is never implicit. It requires explicit `--yes` authorization and registered commands; arbitrary downloaded scripts are not executed.

## Spit Fire bootable ISO

The bundled `boot/bios/first_stage.asm` is built with NASM when available or the built-in bootstrap assembler otherwise. ISO-Tool verifies a 512-byte result with the `0x55AA` signature and inserts it as `boot/bios/first_stage.bin`.

The BIOS El Torito mastering profile explicitly supplies this boot image to xorriso/xorrisofs or Oscdimg, making the generated BIOS ISO boot-configured rather than a data-only ISO.

Generated executables, libraries and BIN/EFI/IMG artifacts are merged into ISO staging under `/bin`, `/lib`, and `/boot-images` before mastering.

## Output controls

The Python GUI provides independent output fields for build root, final ISO file, IMG file, boot-image directory, and executables/libraries. The normal output hierarchy is:

```text
<output>/
├── sources/
├── knowledge/
│   └── repository-tree.json
├── build/
├── staging/
├── iso/
├── img/
├── boot-images/
├── binaries/{executables,libraries}/
├── manifests/
└── logs/
```

The `.img` result is an ISO9660-compatible copy of the generated ISO, not a raw partitioned hard-disk image.

## Chimera II integration

The staged ISO hierarchy preserves `/src`, `/bin`, `/lib`, `/applications/linux`, `/applications/windows`, `/boot`, `/efi`, `/tools`, `/docs`, and `/metadata` where applicable. Spit Fire and other Chimera II boot artifacts are staged according to the selected boot profile.

## Security and reproducibility

Downloaded archives are hashed. Build manifests record source, toolchain, build-system, artifact, boot image, and output information. Imported boot sectors are inert input and are never executed by ISO-Tool. Missing tools and failed build adapters are reported instead of being represented as successful builds.
