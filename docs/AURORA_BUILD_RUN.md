# Aurora Build & Run

## Core build

Aurora is disabled by default so the existing Chimera II host prototype does not require graphical development packages.

```bash
cmake -S . -B build -DAURORA_BUILD=OFF
cmake --build build
ctest --test-dir build --output-on-failure
```

## Aurora build

Install a compatible Wayland development environment and `wayland-server` first. wlroots integration will be enabled in the next compositor milestone after the target wlroots API is selected and validated.

```bash
cmake -S . -B build-aurora -DAURORA_BUILD=ON
cmake --build build-aurora
ctest --test-dir build-aurora --output-on-failure
```

If `wayland-server` is absent, the current foundation intentionally builds a lifecycle stub. This is a build-validation mode, not a functioning compositor session.

## Safe execution

Do not replace an active desktop compositor with this research executable. Test Aurora inside a nested Wayland/X11 environment or a disposable development session.

## Roadmap

1. Pin and validate a wlroots API family.
2. Add backend/renderer/allocator ownership.
3. Add output and input event lifecycles.
4. Add xdg-shell and layer-shell handling.
5. Add rendering/theme/widget services.
6. Integrate Kore device brokering.
7. Add headless and nested integration tests.
