# Command and ISA source/provider audit — 2026-11-09

## Scope and evidence

This audit reads the current canonical repository files:

- `system/commands/chimera-command-list.json`
- `isa/isa_database.json`
- `isa/world_architectures.json`
- `tools/isa/architecture-backends.json`
- `tools/commands/install-command-providers.sh`
- `system/terminals/chimera-terminals.json`
- `aurora/shells/registry.json`
- `opensource/sources.json`

It distinguishes catalogue presence from a built provider, successful compilation, conformance, and native execution. A name in a command list or architecture registry is not evidence that a working executable or backend exists.

## Command catalogue

The current unified catalogue has these entry counts:

| Namespace | Entries |
|---|---:|
| Linux/Bash | 301 |
| macOS | 117 |
| Windows CMD | 161 |
| PowerShell | 142 |
| VBScript | 86 |
| SQL Server | 73 |
| Native Chimera | 90 |
| **Total namespace entries** | **970** |
| Duplicate names across namespaces | 78 |
| **Unique command names** | **892** |

The historical "838 remaining" figure is not derivable from this snapshot without a command-by-command status ledger. Earlier 855/818 counts also differ. Do not subtract one historical count from another or claim 838 implementations complete. The canonical catalogue should be reconciled with a generated provider ledger keyed by normalized command ID and namespace.

SS64 is a command-name/reference index, not a source-code or binary repository. The project policy correctly prohibits treating it as a binary provider. Commands must resolve to one of: a native Chimera implementation, an installed upstream binary, an explicitly acquired official package, or a compatibility entry marked provider-missing. A missing provider must remain visible and must not be replaced by a no-op executable.

### Upstream open-source provider families

The existing source catalogue identifies these primary upstream families:

| Family | Representative commands/capabilities | Upstream |
|---|---|---|
| GNU Coreutils | ls, cat, cp, mv, rm, mkdir, chmod, head, tail, sort, wc | https://www.gnu.org/software/coreutils/ |
| util-linux | mount, fdisk, lsblk, blkid, dmesg, login and terminal tools | https://github.com/util-linux/util-linux |
| findutils | find, xargs, locate | https://www.gnu.org/software/findutils/ |
| GNU grep/sed/gawk/mawk | text search and transformation | https://www.gnu.org/software/grep/ ; https://www.gnu.org/software/sed/ ; https://www.gnu.org/software/gawk/ |
| iproute2 | ip, ss, tc | https://git.kernel.org/pub/scm/network/iproute2/iproute2.git |
| procps/psmisc | ps, top, free, kill, pgrep, fuser | https://gitlab.com/procps-ng/procps ; https://gitlab.com/psmisc/psmisc |
| Toybox/BusyBox | compact multicall utilities | https://github.com/landley/toybox ; https://busybox.net/ |
| Bash/Dash/Zsh/fish/mksh/Yash/Elvish/Nushell | shell language and builtins | https://www.gnu.org/software/bash/ ; https://git.kernel.org/pub/scm/utils/dash/dash.git ; https://www.zsh.org/ ; https://fishshell.com/ ; https://github.com/MirBSD/mksh ; https://yash.osdn.jp/ ; https://elv.sh/ ; https://www.nushell.sh/ |
| OpenSSH/curl/wget/rsync | secure remote access and transfer | https://www.openssh.com/ ; https://curl.se/ ; https://www.gnu.org/software/wget/ ; https://rsync.samba.org/ |
| e2fsprogs/dosfstools/exfatprogs | filesystem tools | https://e2fsprogs.sourceforge.net/ ; https://github.com/dosfstools/dosfstools ; https://github.com/exfatprogs/exfatprogs |
| DOSBox-X | DOS application compatibility runtime | https://github.com/joncampbell123/dosbox-x |

The provider install script currently declares 103 Ubuntu package names. This is a provider package set, not proof that all 301 Linux/Bash commands or the other platform namespaces are available. Some package names are unavailable on a given Ubuntu release; the new report records each package as installed, unavailable, or failed.

The runtime capability generator currently hard-codes 15 names as native Chimera command implementations. The native command catalogue namespace contains 90 entries, so the other names must resolve through a real provider or remain explicitly unavailable. The separate runtime-provider registry declares 284 command/provider associations across POSIX, GNU Coreutils, BusyBox, BSD/macOS, Windows CMD, PowerShell, developer tools, networking, storage, services, DOS and database groups. Those 284 associations are metadata and do not prove that each binary/runtime is installed or behaviorally conformant.

## ISA inventory

The canonical ISA database contains:

- 104 architecture records.
- 154 instruction-form records.
- 61 source references.
- 75 records marked `catalog-only`.
- 14 architecture IDs with any instruction rows.
- 90 architecture IDs with no instruction rows in this database.

Architecture record status distribution:

| Status | Records |
|---|---:|
| project-defined | 2 |
| standard | 15 |
| legacy/standard | 6 |
| legacy | 5 |
| configurable | 1 |
| catalog-only | 75 |
| **Total** | **104** |

The 14 architecture IDs with instruction rows are:

| Architecture ID | Instruction rows |
|---|---:|
| riscv64 | 30 |
| aarch64 | 16 |
| mips32 | 13 |
| x86-64 | 13 |
| 6502 | 12 |
| powerpc | 11 |
| arm32 | 10 |
| z80 | 10 |
| m68k | 9 |
| avr | 9 |
| 8051 | 9 |
| s390x | 4 |
| arm32-thumb | 3 |
| chimera-c8192 | 5 |

The 30-entry world architecture registry is a separate family index and must not be conflated with the 104 detailed database records. The 15-entry backend registry is provider metadata, not 15 complete and tested backends.

The listed backend providers are Clang, LLVM MC, LLVM/GNU objdump, QEMU user-mode, Wine, Darling, Wasmtime and DOSBox-X. Presence/detection is not a guarantee of target ABI, sysroot, linker, runtime, or instruction conformance. In particular, a compiler can emit an object for a target without the target's C library, linker, loader or operating system being available.

### Build and conformance order

The image build now runs `tools/isa/build-architecture-smokes.py`. It attempts freestanding Clang object compilation for every declared LLVM target and a NASM 16-bit DOS `.COM` smoke for `dos-x86`, recording artifact hashes, object headers/file types and failures in `isa-smokes/report.json`. `--full` makes this smoke matrix strict. These are compile-only backend checks, not full OS binaries or instruction conformance tests.

1. Normalize the architecture ID and define exact ISA revision/extensions/ABI.
2. Confirm upstream source/specification provenance and license.
3. Probe the actual assembler/compiler backend for the target triple.
4. Build a freestanding smoke object and inspect ELF/COFF/Mach-O headers.
5. Add sourced instruction decode/encode vectors and semantic tests.
6. Run official architecture tests where available (e.g. RISC-V architectural tests).
7. Run differential tests against a trusted simulator or reference toolchain.
8. Only then mark the architecture conformance-tested.
9. Native hardware boot/runtime verification is a separate final gate.

Do not infer native OS support from a QEMU user-mode test or a successful compile.

## Terminal and shell inventory

The cross-platform system terminal manifest contains 18 terminal applications; the Aurora launch registry now contains 20 entries (the 18 system entries plus Ghostty and Contour). The shell registry contains 8 shells: Bash, Zsh, fish, Dash, mksh, Yash, Elvish and Nushell. These are registry entries. The source-first import scripts and rootfs architecture checks must produce target binaries; a desktop entry or registry record is not proof of an installed, launchable terminal.

## Build gate added in this change

The provider installer now writes a JSON report with package outcomes. Full mode also enables the allowlisted online ISA/command source refresh, source-discovery crawler and RISC-V opcode import; DOS discovery is metadata-only and payload staging downloads only manifest entries that have a reviewed redistribution license, explicit redistributable approval, a pinned SHA-256 and smoke-test status. Best-effort mode remains available for development images. The `--full` release build passes `CHIMERA_STRICT_COMMAND_PROVIDERS=1` into Docker, where missing or failed declared package providers stop the image build rather than silently passing.

This strict gate is intentionally expected to reveal unresolved providers. It does not by itself prove full catalogue coverage; the per-command namespace ledger and ISA-specific conformance matrix remain required.

## Linux reference and cross-compilation notes

As of 2026-11-09, kernel.org lists Linux 7.3.3 as the latest stable release (2026-11-06) and 7.4-rc2 as mainline. Use the stable 7.3.3 source/docs for reproducible compatibility crosswalks; use mainline only for forward-looking research, not as an unpinned release dependency. The 7.2 series is marked end-of-life by the kernel release index. See https://kernel.org/ and https://kernel.org/category/releases.html.

Use Linux as a reference for subsystem contracts, not as a source to copy wholesale into the Chimera kernel. Clang cross-compilation requires a correct target triple and matching target headers/libraries/sysroot. QEMU user-mode execution is useful for testing foreign Linux userspace binaries, but does not prove a target kernel or physical machine boot. Linux's own LLVM build documentation also explicitly distinguishes architectures that the toolchain can target from architectures that build and run successfully.

References:

- LLVM cross-compilation: https://clang.llvm.org/docs/CrossCompilation.html
- LLVM cross-building and sysroots: https://llvm.org/docs/HowToCrossCompileLLVM.html
- Linux kernel LLVM build matrix: https://docs.kernel.org/kbuild/llvm.html
- RISC-V ratified ISA: https://docs.riscv.org/reference/isa/
- DOSBox-X source/license/build information: https://github.com/joncampbell123/dosbox-x

## Release blocker conclusion

No honest "all commands/all ISAs built" claim is supported by the current metadata. The next release evidence must include a generated per-command provider report, target-specific binary hashes and licenses, per-ISA conformance results, and the six immutable-ISO BIOS/UEFI runtime cases. Missing evidence remains a blocker, not a pass.

## 2026-11-09 implementation addendum: X11 provider stack

After the audit snapshot, the Linux command-provider package list was expanded from 103 to 111 packages. The eight additions are `xserver-xorg`, `xinit`, `xauth`, `xwayland`, `xvfb`, `x11-xserver-utils`, `x11-utils`, and `openbox`.

The new `desktop/x11/xorg-provider.json` declares the provider set, and `desktop/x11/start-session.sh` supplies a guarded Aurora/Marine X11 launch path. This is **provider integration, not a verified Koronos X11 runtime**. Linux syscall coverage, DRM/KMS, VT, input and session-management prerequisites remain release gates. The launcher refuses by default until runtime verification is explicitly enabled.
