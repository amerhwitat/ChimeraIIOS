# Chimera II Command Compatibility Framework

Chimera provides four layers:

1. Chimera-native commands
2. POSIX/Linux command compatibility
3. Windows CMD/PowerShell compatibility
4. macOS command compatibility

SS64 is treated as a command-reference source, not as a binary distribution.

Native binaries are compiled by the Chimera builder.

Foreign executable formats are detected before execution:

ELF   -> native/Linux runtime
PE    -> Windows compatibility runtime
Mach-O -> macOS compatibility runtime
script -> interpreter from shebang

A missing compatibility runtime is a controlled error and never silently
pretends that the foreign executable is a native Chimera executable.

Arabic command names are exposed through `/etc/profile.d/chimera-command-compat.sh`.

Examples:

    عرض
    موقعي
    نسخ file1 file2
    حذف file
    مجلد test
    دليل ls

Explicit modes:

    CHIMERA_MODE=native chimera ls
    CHIMERA_MODE=linux chimera grep foo file
    CHIMERA_MODE=macos chimera open .
    CHIMERA_MODE=windows chimera dir
    CHIMERA_MODE=powershell chimera Get-Process

Executable dispatch:

    chimera exec ./program

This layer is intentionally independent from Koronos.
