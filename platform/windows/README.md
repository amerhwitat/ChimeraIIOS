# Windows integration

The Windows layer provides a native setup/build entry point and application-distribution metadata. Windows applications can be represented as MSIX/AppX packages or EXE/MSI installers, while Chimera can invoke a compatibility runtime where supported.

Current Microsoft documentation recommends MSIX for Store distribution and also supports EXE/MSI submission. Chimera therefore keeps package format metadata separate from execution compatibility.

Legacy Windows hosts should use a native bootstrap path when the current .NET runtime is unsupported; the project does not claim that modern .NET runs on every historical Windows release.

## Hosted native services and routing

The portable service utility is tools/hosted/chimera-host-services.py and uses Windows Service Control Manager via sc.exe. Read operations are unprivileged; lifecycle mutations require an elevated administrator token, --apply and CHIMERA-HOST-SERVICE-CHANGE confirmation. Static route/interface operations use route.exe and ipconfig.exe. BareMetal builds may use WSL2 or a native LLVM/Clang, NASM, CMake and Ninja toolchain. Windows drivers and kernel modules are never loaded into Koronos.
