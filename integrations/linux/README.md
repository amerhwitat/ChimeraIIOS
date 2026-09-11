# Linux Compatibility and Source Integration

Chimera II OS integrates Linux functionality through compatibility layers, reviewed open-source components, ABI contracts, and upstream provenance rather than copying all Linux distributions into one kernel tree.

## Coverage model

- Linux/POSIX syscall compatibility
- ELF and standard ABI handling
- proc/sys-style service interfaces where applicable
- device and driver adapter boundaries
- networking and socket compatibility
- filesystems through VFS adapters
- system-service compatibility profiles
- package/distro integration manifests

## Source policy

The Linux kernel is GPL-2.0-only with an explicit syscall exception; individual files may have compatible licenses and must retain their SPDX identifiers. Only individually reviewed, redistributable source may be copied into Chimera II. The complete Linux source tree and every distribution's package universe are not duplicated here.

Distribution support is represented as adapters/manifests for Debian, Ubuntu, Fedora, RHEL-compatible systems, Arch, openSUSE, Alpine, Gentoo, Slackware, Void and other Linux families. This permits Chimera to reproduce relevant interfaces without creating an unmaintainable aggregation of unrelated distro trees.

## Clean implementation

When an upstream implementation is not suitable for direct import, Chimera implements the same documented interface independently. This is especially important for kernel subsystems and the Mobile Microkernel.

## Verification

Each adapter should include:

- ABI/conformance tests
- license/provenance metadata
- architecture capability checks
- syscall/service mapping tables
- negative tests for unsupported behavior

See `docs/SOURCE_IMPORT_POLICY.md`.
