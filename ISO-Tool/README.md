# ISO-Tool

Cross-language desktop ISO/image build orchestrator for Chimera II OS and related repositories, with native Visual Studio 2022/MSVC, WPF/.NET, and Python front ends.

## Synchronized workspace

The ISO-Tool workspace integrates `amerhwitat/ChimeraIIOS`, `amerhwitat/BizX`, and `amerhwitat/BizXtreme`. The standard profile is `engine/repository-profiles.json`; the Python workspace entry point recursively acquires, analyzes, builds, links, stages and masters compatible artifacts while preserving source provenance.

## Toolchain detection before dependencies

The converted Windows detector is `python/iso_tool/toolchain_detector.py`, with `python/detect_toolchains.py` as a standalone entry point. It detects GCC/MinGW, MSVC/MASM, NASM, Go, Rust, Java, Python, LLVM/Clang, LLD, CMake, Ninja, MSBuild, Git, xorriso and Oscdimg. It checks PATH, bounded installation locations and Visual Studio registry roots. Detection runs before dependency resolution and writes a machine-readable toolchain manifest. Environment persistence is opt-in.

## Implementations

- `vcpp/` — native C++/Win32 Visual Studio implementation.
- `dotnet/` — WPF/.NET implementation.
- `python/` — reference engine, detector and workspace entry points.
- `engine/` — profiles and shared build configuration.
- `boot/` — BIOS/UEFI and Spit Fire boot definitions.
- `docs/` — architecture, build, ISO, security and integration documentation.

All language front ends follow the same artifact contract: source is preserved, executables are staged in `/bin`, libraries in `/lib`, boot artifacts in `/boot-images`, and provenance/build reports in `/metadata` or `/manifests`.

## Combined build

```text
cd ISO-Tool/python
python detect_toolchains.py --output <selected-output>\manifests\windows-toolchains.json
python build_workspace.py --output <selected-output> --compiler auto
```

The pipeline is:

`acquire → toolchain detection → dependency checks → recursive source analysis → build plan → compile/assemble/link → artifact collection → Spit Fire boot image → staging → ISO/IMG → verification`

Independent repositories can build in parallel and failures are recorded without incorrectly claiming unavailable artifacts succeeded.

## Boot and artifacts

The Spit Fire first stage is assembled from `boot/bios/first_stage.asm`, validated as a 512-byte boot sector ending in `0x55AA`, and staged under `boot/bios/`. Generated executables, static/shared libraries, binary images and EFI artifacts are retained for inclusion in the ISO when compatible.

## Security

Imported boot sectors and arbitrary downloaded scripts are never executed merely because they are discovered. Package installation requires explicit authorization. Archive traversal/link attacks are rejected. Environment changes from the detector are process-local unless explicitly requested.

The canonical cross-repository integration contract is also available in `tools/ISO-Tool-INTEGRATION.md`.
