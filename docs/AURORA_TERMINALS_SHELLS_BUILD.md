# Aurora Terminals & Shells — Chimera II OS

## Integrated inventory

Aurora now has registries for terminal emulators and command shells.

Terminals: XTerm, GNOME Terminal, Konsole, XFCE Terminal, Foot, Kitty, Alacritty, WezTerm, Ghostty and Contour.

Shells: Bash, Zsh, fish, Dash, mksh, Yash, Elvish and Nushell.

## Acquisition policy

1. Prefer reproducible source builds when a supported compiler/build recipe exists.
2. If source compilation is unavailable, use an upstream distribution package or release binary.
3. Do not accept an unverified downloaded executable. Release-binary acquisition must obtain and verify an upstream checksum/signature before staging.
4. Record source repository, build method, architecture and license in the Aurora manifests.
5. Keep Bash/Dash available for POSIX/Bourne compatibility; alternative shells are opt-in.

## Build hook

`build-chimera-iso.sh` should execute `scripts/chimera-iso-terminal-shell-hook.sh` after `CHIMERA_ROOTFS_DIR` has been created and before the root filesystem is compressed into squashfs.

The hook calls `scripts/import-aurora-terminal-shell-suite.sh`, stages the Aurora desktop entries and installs the shell launcher.

For a standalone ISO-rootfs staging test:

```bash
CHIMERA_ROOTFS_DIR=/path/to/iso/rootfs \\
  bash scripts/chimera-iso-terminal-shell-hook.sh
```

## Current upstream build facts

- Alacritty is an open-source Rust/OpenGL terminal and publishes its source with Apache-2.0/MIT licensing.
- WezTerm is a Rust GPU terminal/multiplexer and documents `cargo build --release` as its source-build path.
- Ghostty provides source tarballs and uses Zig; the required Zig version is tied to each Ghostty version.
- Contour is an Apache-2.0 C++ terminal with CMake presets.
- Nushell publishes Linux release builds and source; the current release page provides architecture-specific artifacts.
- Elvish publishes source and statically linked binaries and documents its BSD-based licensing with component exceptions.
- Fish provides a source tree and documents its mixed GPL/LGPL/MIT/PSF licensing.

Sources used for the registry/build design are the upstream project repositories and documentation linked in `aurora/terminals/registry.json`, `aurora/shells/registry.json`, and the build manifests.
