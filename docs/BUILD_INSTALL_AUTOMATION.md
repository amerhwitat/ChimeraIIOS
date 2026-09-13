# Chimera II OS Build, Dependency, Packaging and Installer Automation

Chimera II OS now has a single build orchestration contract exposed through Python, POSIX shell, Windows CMD, and PowerShell. GitHub Actions uses the same entry point so local and CI builds follow the same configuration/test/package sequence.

## Entry points

- `python tools/build/orchestrator.py doctor` — inspect available toolchains.
- `python tools/build/orchestrator.py deps` — install dependencies declared by repository manifests.
- `python tools/build/orchestrator.py configure` — generate an out-of-source CMake build tree.
- `python tools/build/orchestrator.py build` — compile native targets.
- `python tools/build/orchestrator.py test` — execute CTest.
- `python tools/build/orchestrator.py package` — invoke CPack.
- `python tools/build/orchestrator.py install` — stage an install tree below the build directory.
- `python tools/build/orchestrator.py all` — dependency, configure, build, test and package pipeline.

Equivalent wrappers are provided under `scripts/` for `.sh`, `.cmd`, and `.ps1` environments.

## Supported language families

The build manifest tracks C/C++/ASM, Rust, Python, Node.js/TypeScript, Java, .NET/C#, Kotlin, Swift, and Dart. The orchestrator intentionally discovers only language trees that actually exist in the checkout and prefers committed lockfiles/manifests.

## Packaging

CMake/CPack produces portable archives and, when the generator/toolchain is available, native Linux packages, Windows NSIS installers, and macOS disk images. Package generation is separate from the OS installer planner.

## Safety

Dependency installation uses named package-manager commands rather than executing downloaded scripts. Driver, firmware, bootloader, partitioning, filesystem-formatting, and other destructive operations remain outside the default application packaging path and require explicit authorization through the existing installer planning layer.

## CI

The cross-platform workflow builds on Linux, Windows, and macOS, runs tests before packaging, and uploads build/package artifacts. GitHub Actions supports OS matrices and platform-specific hosted runners, while CMake selects the appropriate generator for each host. citeturn0search4turn0search8

## Reproducibility

Use `--dry-run` to inspect commands, `--build-dir` to isolate build trees, and committed lockfiles where available. CI should pin toolchain versions where a component has a hard compatibility requirement.
