# Chimera II OS — Cross-Platform Command Compatibility

Chimera II now exposes a unified command namespace for common POSIX/Linux/Unix, BSD/macOS, Windows CMD, and PowerShell command names.

## Behavior

1. Native command first.
2. Compatibility spelling second.
3. If a platform-specific executable is absent, Chimera reports it as unavailable rather than fabricating behavior.
4. Privileged operations remain subject to Koronos/Aegis authorization.
5. English names remain valid when Arabic command aliases are enabled.
6. The catalog is data-driven in system/commands/command_compatibility.json.

PowerShell is a cross-platform shell and automation language for Windows, Linux, and macOS. Windows CMD remains a separate command interpreter. Microsoft also publishes a Windows Coreutils package containing common Unix-style utilities. citeturn0search10turn0search1turn0search4

Apple's Command Line Tools provide macOS terminal-oriented development and automation tooling; Chimera catalogs compatible command names without redistributing Apple's proprietary binaries. citeturn0search6

## Command families

Filesystem, text processing, environment, processes, services, accounts, networking, storage, archives, security/crypto, development, Windows compatibility, macOS compatibility, and Chimera-native administration are included in the catalog.

## Arabic

Arabic aliases map to the canonical command namespace. Examples include:

- مساعدة -> chmhelp
- اعرض -> ls
- انسخ -> cp
- انقل -> mv
- احذف -> rm
- ابحث -> grep
- شبكة -> ip
- اختبر-اتصال -> ping
- دليل -> man
- إعادة-تشغيل -> chm-reboot

The command-language setting can select Arabic or English while retaining English command names for compatibility.

## Implementation boundary

This is a compatibility namespace, not a claim that all Linux, Windows, macOS, or Unix software has been copied into Chimera. Proprietary platform binaries and licensed source are not imported merely because their command names are listed. Open-source implementations can be integrated package-by-package with their licenses and build metadata preserved.
