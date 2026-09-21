# Building the SDK

From the repository root:

    cmake -S . -B build/sdk
    cmake --build build/sdk --target chimera_sdk chimera-sdk-config

Java:

    ./sdk/java/build.sh

C#:

    dotnet build sdk/csharp/Chimera.Sdk.csproj

Python:

    python3 -m compileall sdk/python/chimera_sdk

Objective-C:

    clang -fsyntax-only sdk/objective-c/ChimeraSDK.m

The final ISO build invokes the SDK build as part of its source/package stage. Native compiler and runtime packages are supplied by the target build environment.
