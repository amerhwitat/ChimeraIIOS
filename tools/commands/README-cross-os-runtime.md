# Cross-OS command registry and runtime policy

ChimeraIIOS and OctavianOS use one metadata registry for command discovery and a
single dispatcher (chimera-run) for explicit native/compatibility selection.

## Modes

- `chimera-run --mode native PROGRAM [ARG...]`: execute a native ELF for the
  running ISA or an executable script with a shebang. No foreign-OS fallback.
- `chimera-run --mode compat PROGRAM [ARG...]`: execute native inputs as usual,
  or dispatch recognized foreign formats through a provider already installed on
  the system (QEMU user emulation, Wine, DOSBox, Darling, or Wasmtime/Wasmer).
- `chimera-run PROGRAM [ARG...]`: auto mode, preferring native execution and
  using a provider only for a recognized foreign executable.
- `chimera-run --list`: print the command-family catalog and runtime expectations.

The dispatcher preserves argv and uses exec APIs; it does not pass user input
through a shell. It never downloads binaries, silently elevates privileges, or
pretends that a catalog entry means a command is installed.

## Command coverage

The JSON catalog inventories common POSIX/GNU, BusyBox, BSD/macOS, Windows CMD,
PowerShell, DOS/retro, developer, networking, storage, system-service, database,
and Chimera-native command families. It is an extensible index, not a claim that
every command from every OS is shipped or fully compatible. The effective command
set is the intersection of registry entries, installed providers, permissions,
and tested behavior.

## Current build evidence (2026-11-07)

- The generated capability manifest contains 4,141 command/platform records and
  distinguishes native, shell-builtin, native-provider-required, and
  compatibility-provider-required entries.
- The native Linux userspace multicall currently implements 25 POSIX command
  aliases. The same source is cross-built and ELF-machine-validated for
  x86-64, i686, armel, AArch64, ARMv7, RISC-V 64, PowerPC64LE, and s390x.
- CI runs QEMU-user smoke tests for those eight Linux ABIs. This is Linux
  userspace validation only; these binaries are **not Koronos syscall-ABI
  binaries**.
- The 90-entry Chimera-native command catalogue is tracked separately. Hosted
  Linux frontends or package providers do not count as Koronos-native
  implementations. Missing backends remain explicitly marked as candidates or
  provider-required until a real implementation and runtime test exist.
- The ISA index remains discovery metadata. Instruction encodings, semantics,
  privileged operations, and per-architecture conformance are separate gates.

## Binary and provider policy

Keep Chimera-native executable wrappers and generated native binaries under
tools/commands/ (and stage runtime payloads under the ISO's native command
directory). Do not commit opaque binaries copied from other operating systems.
Acquire compatible runtimes and upstream tools through their own license-aware,
hash-verified package/build workflows. The dispatcher can invoke an installed
provider; it does not implement Wine, QEMU, PowerShell, a BSD kernel, or Windows
subsystems by itself.

Foreign formats recognized by the dispatcher: PE/COFF, ELF for another ISA, DOS
MZ, Mach-O, and WebAssembly. A handler is available only if a compatible provider
is installed. Some Mach-O variants and architectures may require additional
format validation and are not automatically assumed runnable.

## Release truthfulness

“Cataloged”, “installed”, “native”, “emulated”, “compatibility-tested”, and
“userspace-ready” are separate states. Never promote a command to tested or
supported merely because it appears in this catalog. Privileged disk, network,
process, and service operations remain subject to OS permissions and confirmation.
