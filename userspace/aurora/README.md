# Aurora Wayland

Aurora is the Chimera II graphical userspace layer. It is designed to sit above Koronos/Kore and provide a modern Wayland desktop/compositor boundary.

## Status

This directory is an engineering foundation. The existing `desktop/aurora/` research implementation remains unchanged. The userspace implementation is intentionally dependency-gated because wlroots APIs differ across releases.

## Components

- `compositor/` — compositor executable and graphical service interfaces.
- `demo/` — optional visual/demo material, not the compositor itself.
- `packaging/` — Kore/systemd/desktop-session metadata.

## Build

The repository root exposes `AURORA_BUILD`, default `OFF`, so core Chimera II builds remain independent of graphical host dependencies.

```bash
cmake -S . -B build -DAURORA_BUILD=OFF
cmake --build build
ctest --test-dir build --output-on-failure
```

When wlroots and the required Wayland development packages are installed:

```bash
cmake -S . -B build-aurora -DAURORA_BUILD=ON
cmake --build build-aurora
ctest --test-dir build-aurora --output-on-failure
```

Do not run an experimental compositor directly on a production display session. Prefer a nested Wayland/X11 test environment until the backend and protocol versions have been validated.
