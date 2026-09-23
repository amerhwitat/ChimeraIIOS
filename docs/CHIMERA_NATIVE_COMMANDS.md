# Chimera II OS Native Commands

The native command layer is intentionally small, inspectable and scriptable.

| Command | Purpose |
|---|---|
| `chmctl` | System control gateway |
| `aurora-settings` | Aurora Desktop settings |
| `chm-diagnostics` | Diagnostics and device/mount inspection |
| `chmhelp` | Native command help |
| `chimera-utils` | Filesystem/text utility multiplexer |
| `chimera-shell` | Chimera command interpreter |

## Shell builtins

Chimera Shell exposes `chmctl`, `aurora-settings`, and `chm-diagnostics` in addition to its existing core builtins.

The implementation deliberately separates the native Chimera command ABI from compatibility shells. Bash, POSIX, Zsh, PowerShell, Cmd and other dialects can coexist without making their proprietary implementations part of Chimera.

## Manual pages

Source man pages live in `man/` and are installed to `share/man/man1` by the userland CMake build.
