# ISO-Tool build entry points

ISO-Tool is a multi-language image construction, dependency, boot-entry and packaging tool used by Chimera II OS.

## C++ / MSVC

Start in `vcpp/` or run:

```bat
build-msvc.bat Release
```

The checked-in Visual Studio solution is `vcpp/ISO-Tool-UnifiedGui.sln`.

## GNU / Linux

```bash
./build-gcc.sh Release
```

If a native CMake engine is present it is built; otherwise use the language-specific directories.

## Other implementations

- `python/` — reference automation and packaging.
- `java/` — JVM implementation.
- `dotnet/` — .NET implementation.
- `vcpp/` — Visual C++ implementation.
- `engine/` — shared/native engine components.
- `gui/` — GUI front ends.
- `tools/` — auxiliary image/boot tooling.

Build artifacts belong under `build/`, `dist/` or CI artifacts. Do not commit generated ISO images unless explicitly intended as a release artifact.
