# Chimera II OS SDK

The SDK is a common developer contract for C, C++, C#, Objective-C, Java/JVM and Python applications.

C/C++ use GCC or Clang with Chimera headers and CMake toolchains. C# uses the .NET SDK/Roslyn toolchain. Objective-C uses Clang and a target runtime profile. Java uses javac and a JVM. Python uses CPython plus the bundled chimera_sdk package.

The repository contains Chimera SDK source, headers, integration code, examples and manuals. It does not silently vendor complete GCC, LLVM, .NET, OpenJDK or CPython source trees; their upstream distributions remain separately licensed and are described by the provenance manifest.
