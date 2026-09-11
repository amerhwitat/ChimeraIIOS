# ISO-Tool

Cross-language desktop ISO/image build orchestrator for Chimera II OS and related repositories, with native Visual Studio 2022/MSVC, WPF/.NET, and Python front ends.

## Synchronized workspace

The ISO-Tool workspace integrates `amerhwitat/ChimeraIIOS`, `amerhwitat/BizX`, and `amerhwitat/BizXtreme`. The standard profile is `engine/repository-profiles.json`; the Python workspace entry point recursively acquires, analyzes, builds, links, stages and masters compatible artifacts while preserving source provenance.

## Toolchain and dependency detection before build planning

The converted Windows detector is `python/iso_tool/toolchain_detector.py`, with `python/detect_toolchains.py` as a standalone entry point. The new stdlib-only `python/iso_tool/dependency_detector.py` adds a broader inventory for Git, Python, GCC/G++, MSVC, Clang/LLD, NASM/MASM, CMake/Ninja/MSBuild/Make, xorriso/Oscdimg, QEMU, Java/javac, .NET, Node/npm, Go, Rust and archive tools. Detection runs before dependency/build planning and records required/optional gaps without silently changing PATH.

## Python → C++ / C# / Java parity

The Python tree remains the feature-complete reference. C++17, C# (`net48` and `net6.0-windows`) and Java 8+ now contain typed dependency and recursive Python-parity services under `vcpp/`, `dotnet/ISO-Tool/`, and `java/`. This is a semantic conversion rather than an unsafe line-by-line rewrite of Python's dynamic semantics. Every Python source file remains discoverable; dynamic-only behavior is represented by an explicit typed service boundary and diagnostic.

See `docs/PYTHON_TO_MULTILANGUAGE_PARITY.md`, `docs/DEPENDENCY_MATRIX.md`, and `engine/python-parity-manifest.json`.

## Implementations

- `vcpp/` — native C++/Win32 Visual Studio implementation and parity services.
- `dotnet/` — WPF/.NET implementation and parity services.
- `java/` — Java 8-compatible CLI/core parity implementation.
- `python/` — reference engine, detector and workspace entry points.
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

`acquire → toolchain/dependency detection → recursive source analysis → build plan → compile/assemble/link → artifact collection → Spit Fire boot image → staging → ISO/IMG → verification`

Independent repositories can build in parallel and failures are recorded without incorrectly claiming unavailable artifacts succeeded.

## Boot and artifacts

The Spit Fire first stage is assembled from `boot/bios/first_stage.asm`, validated as a 512-byte boot sector ending in `0x55AA`, and staged under `boot/bios/`. Generated executables, static/shared libraries, binary images and EFI artifacts are retained for inclusion in the ISO when compatible.

## Security

Imported boot sectors and arbitrary downloaded scripts are never executed merely because they are discovered. Package installation requires explicit authorization. Archive traversal/link attacks are rejected. Environment changes from the detector are process-local unless explicitly requested.

The canonical cross-repository integration contract is also available in `tools/ISO-Tool-INTEGRATION.md`.
