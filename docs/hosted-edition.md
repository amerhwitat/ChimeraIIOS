# Chimera II OS Hosted Edition

## Purpose

Hosted Edition runs Chimera user-space tools on top of a 64-bit Windows, Linux, BSD/POSIX or macOS host. It extends the host with a common command bridge, host/ISA discovery and Aurora desktop-open integration. It does **not** replace the host kernel, boot Koronos, virtualize an entire machine, or provide a complete Win32/POSIX/Darwin ABI emulator.

## Install and try

After installing Chimera:

```sh
chimera-hosted info
chimera-hosted compat list
chimera-hosted isa
chimera-hosted desktop-info
chimera-hosted translate --mode windows ls
chimera-hosted run --mode linux -- echo "Hello from Chimera"
chimera-hosted open .
```

From a source checkout, replace `chimera-hosted` with `python3 tools/runtime/chimera-hosted.py`.

The bridge offers portable built-ins (`pwd`, `ls/dir`, `echo`, `cat/type`, `mkdir`, `cp/copy`, `mv/move`, `rm/del`, `whoami`, `uname`, `env/set`, `clear/cls`) and a limited alias table. External programs are started with argument arrays and `shell=False`. The bridge intentionally does not parse shell pipelines, redirection, command substitution or job control. It refuses recursive directory deletion.

## Host OS and ISA matching

The runtime detects the actual host OS and CPU ISA, then matches aliases to canonical IDs in `isa/isa_database.json` (for example, AMD64/x86_64 to `x86-64`, and AArch64/arm64 to `armv9-a64`). A matching inventory row only identifies the CPU family. It does not mean a compiler backend, binary loader or emulator exists for that ISA. Guest instructions may execute only through a validated decoder/backend.

## OS-specific boundaries

- **Windows x64:** native Windows programs use Windows' own PE loader when run on Windows. Chimera's PE compatibility tooling validates image headers; the native PE runner and broad Win32 API implementations are separate work. Windows-specific assembly that calls Win32 APIs cannot be made portable merely by changing instruction syntax.
- **Linux x64/ARM64:** uses the Linux/POSIX host ABI and `xdg-open` when available. This bridge is not a Linux syscall emulator.
- **BSD/POSIX Unix:** uses installed host commands and POSIX interfaces. BSD-specific extensions remain host-dependent.
- **macOS Intel/Apple Silicon:** uses the Darwin/POSIX host ABI and the `open` command. Code signing, entitlements, app sandboxing, and Darwin-specific APIs remain governed by macOS.

## Aurora desktop

`chimera-hosted open PATH_OR_URL` delegates to the host's default opener (`os.startfile`, `open`, or `xdg-open`). The desktop-info action exposes bridge capabilities to a launcher. It does not claim that the Aurora Wayland compositor already runs natively on Windows or macOS; a platform-native Aurora backend and GUI integration still need implementation and testing.

## Assembly source integration

The repository did not contain a file named `win-asm.txt` at the time of this change, and the available conversation/library search did not locate it. Its exact source cannot be imported faithfully until it is added to the repository or attached. No assembly instructions or Win32 API code are fabricated as a substitute. The current compatibility boundary can identify the host ISA, but assembling/linking and executing MASM/NASM or Windows-API assembly requires a compatible assembler/linker, matching target ABI, and any required Win32 API runtime.

## Security

- No `shell=True` invocation or implicit shell interpolation.
- No copying of proprietary Windows system DLLs.
- Cross-ISA execution is refused unless an explicit validated backend is available.
- Untrusted native executables require OS-level isolation and must not be treated as safe merely because their file format parses.

## 32-bit hosted profile

The hosted bridge supports a 32-bit interpreter profile on Windows x86, Linux x86 and BSD/POSIX x86 when a compatible Python 3 runtime and host tools are available. `chimera-hosted info` reports process pointer width and detected host ISA. The bridge does not need 64-bit pointers merely to run its Python user-space commands.

This is not a 32-bit native Koronos kernel port. A 32-bit process/OS cannot natively load 64-bit executables, 64-bit shared libraries, 64-bit drivers or a 64-bit kernel. Use matching 32-bit compilers, linkers and dependencies. Cross-ISA or cross-bitness execution requires a separately validated emulator/backend. Current macOS support remains 64-bit only.

```sh
python3 tools/runtime/chimera-hosted.py info
python3 tools/runtime/chimera-hosted.py compat list
python3 tools/runtime/chimera-hosted.py isa
```

A successful bridge run does not prove that every CMake target, native driver, Aurora compositor or ISO boot path builds on a 32-bit host; those require separate build and runtime validation.
