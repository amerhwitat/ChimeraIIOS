# Chimera II OS Windows setup

The Windows setup is a **host-side installer/upgrade bootstrapper**, not a replacement for Windows Setup. It detects architecture and Windows version, installs or launches the appropriate Chimera II managed/native components, and preserves rollback boundaries.

Compatibility policy:

| Host | Native bootstrap | .NET 8/9/10 |
|---|---|---|
| Windows 11 x64/x86/Arm64 | supported where OS architecture permits | supported |
| Windows 10 supported editions | supported | supported by the corresponding Microsoft .NET support matrix |
| Windows Server supported releases | supported | supported according to .NET matrix |
| Windows 8.1 / Windows 7 | legacy native bootstrap only | modern .NET 8+ is not supported |

The installer must never claim that .NET 8+ runs on unsupported Windows versions. On unsupported hosts it reports the limitation and can offer a native compatibility package when one is produced for that target.

The setup can be packaged with WiX/MSI or another signed Windows installer system. Production releases should be Authenticode-signed and should validate the ISO/installer SHA-256 before execution.
