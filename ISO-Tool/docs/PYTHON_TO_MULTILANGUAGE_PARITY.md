# ISO-Tool language parity and dependency inventory

The Python implementation remains the reference orchestrator. C++17, C# (`net48`/`net6.0-windows`) and Java 8+ now contain typed parity services for dependency detection and recursive Python-source inventory.

Dependency detection runs before dependency/build planning and covers Git, Python, C/C++ compilers, MSVC, Clang/LLD, NASM/MASM, CMake/Ninja/MSBuild/Make, xorriso/Oscdimg, QEMU, Java, .NET, Node/npm, Go, Rust and archive tools. Missing optional tools are reported without preventing fail-forward planning; required gaps remain explicit.

The conversion is semantic rather than a blind line-for-line rewrite. Python's dynamic features are represented by typed target-language services and stable JSON manifests. This keeps C++, C# and Java independently auditable and compatible with the same artifact, boot, provenance and verification contracts.
