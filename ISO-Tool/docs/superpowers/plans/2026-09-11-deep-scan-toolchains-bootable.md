# Deep Scan, Toolchain Bootstrap, and Bootable ISO Plan

## Goal
Make ISO-Tool recursively inspect the entire acquired repository tree, detect Windows compiler/assembler toolchains, provide a dependency-free Spit Fire BIOS bootstrap when an assembler is absent, build/integrate NASM and GNU C++ when host prerequisites permit, and create a genuinely boot-configured ISO from the Spit Fire first-stage sector.

## Implementation

1. Recursively index every file and directory into `knowledge/repository-tree.json` with SHA-256, language, build-system, artifact, image, and script classifications.
2. Discover MSVC/MASM, LLVM/LLD, GNU/MinGW, GAS/LD, NASM/YASM, CMake/MSBuild/Make, and ISO mastering tools on Windows.
3. Add a constrained built-in assembler for the known one-sector Spit Fire BIOS stage and prefer real NASM whenever available.
4. Add NASM source-build support using upstream Windows/MSVC or MinGW build entry points and record GCC source bootstrap requirements rather than silently executing arbitrary downloads.
5. Recursively discover registered build systems and compile independent nested projects with GNU/MSVC profiles.
6. Merge generated executables, libraries, EFI/BIN/IMG artifacts, and boot images into ISO staging.
7. Build the Spit Fire BIOS first-stage binary, require 512 bytes plus `0x55AA`, and pass it explicitly to ISO mastering through the BIOS El Torito profile.
8. Verify the Python scanner/boot fallback through CI.

## Safety
Downloaded source and archives are treated as untrusted input. Repository scripts are not executed merely because they are present. Package installation remains an explicit user action.
