# Apple applications

This directory is the Apple source/build boundary for Chimera II OS.

- `iOS/` — iPhone/iPad source integration notes.
- `macOS/` — native macOS integration notes.
- `Shared/` — Swift Package Manager shared source.
- `scripts/` — Xcode build/archive/export automation.
- `Config/` — non-secret build/export examples.

A real IPA is produced on macOS with Xcode. Windows/Linux can prepare and dispatch the same source tree but cannot substitute for Apple's toolchain.
