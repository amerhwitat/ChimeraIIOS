# ISO-Tool integration

Chimera II OS is an input repository for the `amerhwitat/nlp/ISO-Tool` workspace builder. The ISO-Tool pipeline detects host toolchains before dependency resolution, recursively analyzes compatible source trees, builds available targets with GNU/MSVC policies, preserves source provenance, stages executables/libraries/boot artifacts, and creates the combined ISO/IMG workspace.

## Standard integration repositories

- ChimeraIIOS — operating system and native toolchain targets
- BizX — application platform
- BizXtreme — game/application target

## Artifact contract

Compatible generated executables belong in `bin/`, libraries in `lib/`, boot artifacts in `boot-images/`, and preserved source trees in `src/<repository-id>/`. The workspace manifest records repository URLs, build results, failures, and provenance.

## Toolchain detection

The ISO-Tool Python detector runs before dependency checks and supports GCC/MinGW, MSVC/MASM, NASM, Go, Rust, Java, Python, LLVM/Clang, LLD, CMake, Ninja, MSBuild, Git, xorriso, and Oscdimg. Environment persistence is opt-in.

This document is an integration contract; it does not duplicate the ISO-Tool implementation.
