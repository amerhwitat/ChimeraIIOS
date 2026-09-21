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
