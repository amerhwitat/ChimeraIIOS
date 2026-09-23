# Chimera II Toolchain Setup

Set CHIMERA_SDK_ROOT to /opt/chimera-sdk after installation.

C/C++:
  export PATH="$CHIMERA_SDK_ROOT/bin:$PATH"
  chimera-cc source.c -I"$CHIMERA_SDK_ROOT/include"
  chimera-cxx source.cpp -I"$CHIMERA_SDK_ROOT/include"

C#:
  dotnet build project.csproj

Objective-C:
  chimera-objc source.m

Java:
  chimera-javac source.java
  chimera-java Main

Python:
  chimera-python application.py

The wrappers select host toolchain executables and provide the Chimera SDK contract. Cross compilation requires a target compiler/sysroot supplied by the selected architecture profile.

## Native C/C++/ASM and linkers

The native baseline is GCC + GNU Binutils, with Clang/LLVM + LLD and NASM available when installed.

  export CHIMERA_SDK_ROOT=/opt/chimera-sdk
  export PATH="$CHIMERA_SDK_ROOT/bin:$PATH"
  chimera-cc hello.c -o hello
  chimera-cxx hello.cpp -o hello-cxx
  chimera-gas -o startup.o startup.s
  chimera-ld startup.o -o startup

Driver selection:
  CHIMERA_NATIVE_COMPILER=gcc|clang
  CHIMERA_NATIVE_LINKER=bfd|lld
  CHIMERA_ASSEMBLER=gnu|llvm|nasm

The existing `chimera-as` executable remains the Chimera ISA assembler and is not replaced by the GNU assembler driver. The GNU assembler driver is named `chimera-gas` to keep the two toolchains unambiguous.

For cross compilation, set CHIMERA_TARGET and CHIMERA_SYSROOT to a registered target compiler/sysroot. Native mode means the generated executable targets the running host ISA; it does not imply that host CPUs have Chimera's wide virtual RegisterN registers.
