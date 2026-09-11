# Dual GNU C++ / MSVC build policy

ISO-Tool validates Windows C++ sources with both GNU C++ and Microsoft Visual C++.

- GNU: MSYS2 UCRT64 MinGW-w64 GCC (`mingw-w64-ucrt-x86_64-gcc`)
- Microsoft: Visual Studio 2022 MSVC x64 (`cl.exe`)

UCRT64 is preferred for GNU Windows builds because MSYS2 identifies it as the recommended environment and documents better compatibility with the UCRT used by current MSVC. Separate build trees are mandatory because CRT/object-library boundaries must not be mixed.

If GNU C++ is missing, the dependency manager creates an explicit official MSYS2 acquisition plan and caches dependencies under `%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool\\dependencies\\msys2`. Arbitrary internet scripts are never executed.

Each compiler build records compiler/version, target, standard, flags, linker, artifacts, and result. MSVC remains the primary native Win32 GUI build while GNU C++ provides independent portability and compatibility validation.
