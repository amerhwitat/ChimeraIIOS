# ISO-Tool

Cross-language desktop ISO/image build orchestrator for Chimera II OS and related repositories, with native Visual Studio 2022/MSVC, WPF/.NET, Java 8+, and Python front ends.

## Synchronized workspace

The ISO-Tool workspace integrates `amerhwitat/ChimeraIIOS`, `amerhwitat/BizX`, and `amerhwitat/BizXtreme`. The standard profile is `engine/repository-profiles.json`; the Python workspace entry point recursively acquires, analyzes, builds, links, stages and masters compatible artifacts while preserving source provenance.

## Toolchain and dependency detection before build planning

The converted Windows detector is `python/iso_tool/toolchain_detector.py`, with `python/detect_toolchains.py` as a standalone entry point. The dependency inventory covers Git, Python, GCC/G++, MSVC, Clang/LLD, NASM/MASM, CMake/Ninja/MSBuild/Make, xorriso/Oscdimg, QEMU, Java/javac, .NET, Node/npm, Go, Rust and archive tools. Detection runs before dependency/build planning and records required/optional gaps without silently changing PATH.

## Python → C / C++ / C# / Java parity

Every Python module is recursively parsed with `python/iso_tool/source_translator.py` during the build preflight. It generates deterministic C, C++, C# and Java parity units and a SHA-256 manifest under `generated/python-parity`. The native targets use C11 metadata, C++17 as the portable baseline (C++20 where supported), a common .NET 6/.NET Framework 4.8-compatible API surface where practical, and Java 8+.

This is a semantic-safety mechanism, not a claim that Python's dynamic runtime can be translated line-for-line. Imports, classes, functions and source hashes are preserved; dynamic constructs require explicit native implementation and behavioral contract tests before they are considered complete.

See `docs/PYTHON_TO_C_CPP_CSHARP_JAVA.md`, `docs/PYTHON_TO_MULTILANGUAGE_PARITY.md`, `docs/DEPENDENCY_MATRIX.md`, and `engine/python-parity-manifest.json`.

## Implementations

- `vcpp/` — native C++/Win32 Visual Studio implementation and parity services.
- `dotnet/` — WPF/.NET implementation and parity services.
- `java/` — Java 8-compatible CLI/core implementation and parity services.
- `python/` — reference engine, detector, AST parity generator and workspace entry points.
- `engine/` — profiles and shared build configuration.
- `boot/` — BIOS/UEFI and Spit Fire boot definitions.
- `docs/` — architecture, build, ISO, security, dependency and parity documentation.

All language front ends follow the same artifact contract: source is preserved, executables are staged in `/bin`, libraries in `/lib`, boot artifacts in `/boot-images`, and provenance/build reports in `/metadata` or `/manifests`.

## Combined build

```text
cd ISO-Tool/python
python detect_toolchains.py --output <selected-output>\manifests\windows-toolchains.json
python build_workspace.py --output <selected-output> --compiler auto
```

The pipeline is:

`acquire → toolchain/dependency detection → Python AST parity generation → recursive source analysis → build plan → compile/assemble/link → artifact collection → Spit Fire boot image → staging → ISO/IMG → verification`

Independent repositories can build in parallel and failures are recorded without incorrectly claiming unavailable artifacts succeeded.

## Boot and artifacts

The Spit Fire first stage is assembled from `boot/bios/first_stage.asm`, validated as a 512-byte boot sector ending in `0x55AA`, and staged under `boot/bios/`. Generated executables, static/shared libraries, binary images and EFI artifacts are retained for inclusion in the ISO when compatible.

## Security

Imported boot sectors and arbitrary downloaded scripts are never executed merely because they are discovered. Package installation requires explicit authorization. Archive traversal/link attacks are rejected. Environment changes from the detector are process-local unless explicitly requested.

The canonical cross-repository integration contract is also available in `tools/ISO-Tool-INTEGRATION.md`.
