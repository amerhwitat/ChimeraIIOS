# Chimera II OS — Visual C++ / MSVC

This tree is the Windows-native implementation layer. It is intentionally separate from the portable `src/cpp/` implementation.

- MSVC / Visual Studio 2022 toolchain
- C++20 baseline
- Win32 bootstrapper and installer-facing native code
- Optional Qt 6 desktop front end
- Shared JSON/JSONL interoperability contracts
- Native bridge for C#, Java, Node.js and Python processes

Boot-critical code remains freestanding C/C++/assembly and is not dependent on the .NET runtime.
