# Deep Recursive Scan, Windows Toolchains, and Spit Fire Boot

ISO-Tool now treats a source repository as a hierarchical build graph rather than a single top-level project.

## Recursive source tree

`tree_scanner.py` walks every directory and records a deterministic tree with file size, SHA-256, source language, build-system markers, image files, artifacts, and scripts requiring review. The resulting `knowledge/repository-tree.json` is the authoritative scan record. Discovered scripts are never executed merely because they exist.

## Windows toolchain discovery

The Windows detector searches PATH, environment variables, and Visual Studio registry locations for MSVC/Link/MASM, LLVM/LLD, GNU/MinGW GCC/G++, GAS/LD, NASM/YASM, CMake/MSBuild/Make, and ISO mastering tools. A machine-readable report is written to `manifests/windows-toolchains.json`.

If NASM is absent, the boot pipeline uses the dependency-free Spit Fire bootstrap assembler for the bundled one-sector BIOS stage. The toolchain bootstrap plan also records how NASM can be built from its official source using `nmake`/MSVC or the MinGW/Unix-style build flow.

## GNU C++ integration

The detector records an existing G++/GCC installation and makes it available to the GNU build profile. If it is absent, the bootstrap plan records GCC as a source-built toolchain target rather than silently installing or executing arbitrary third-party scripts. A complete GCC bootstrap remains dependent on the host prerequisites required by GCC itself.

## Bootable ISO

The image pipeline builds `ISO-Tool/boot/bios/first_stage.asm` as the Spit Fire first-stage sector. NASM is preferred; the built-in bootstrap assembler is the fallback. The result must be exactly 512 bytes and end in `0x55AA`.

The staging tree receives `boot/bios/first_stage.bin`, and ISO mastering uses the `bios-only` El Torito profile. The `.img` output is an exact copy of the generated ISO and is therefore an optical-image-compatible IMG, not a raw partitioned hard-disk image.

## Build hierarchy

Nested CMake, Make, Meson, Cargo, npm, Maven, Gradle, .NET, and Autotools projects are discovered recursively. Registered build adapters compile each supported project with GNU and MSVC profiles when the required tools are available. Unsupported projects are recorded instead of being treated as arbitrary shell scripts.
