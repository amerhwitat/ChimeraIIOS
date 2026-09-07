# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research and engineering prototype. This repository separates host-emulated components from future bare-metal firmware, kernel, driver, FPGA, and silicon work.

## Live demonstrations

- **CodeWords / shared HTML demo:** https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- **OnHercules live demo:** https://chimera-ii-os-730893.onhercules.app/

See [`docs/DEMO_SITES.md`](docs/DEMO_SITES.md) for synchronization and source-import status.

## Architecture

```text
Firmware / UEFI / BIOS
        |
        v
 Spit Fire boot stages --> Jasper boot manager
        |
        v
 Koronos microkernel
        |
 +------+---------+----------+---------+
 |      |         |          |         |
 v      v         v          v         v
Kore  Spotnik     VFS        Hive    Nucleus
 |      |          |          |         |
 +------+----------+----------+---------+
                    |
                    v
             Aurora Desktop
          Wayland + Vulkan/OpenGL
                    |
                    v
       Applications / CEF / POSIX / Win32

       +-------------------------------+
       | R8192 / C8192 / RegisterN    |
       | 4096 -> 8192 -> N-bit        |
       +-------------------------------+
                    |
                    v
          128D / neural / observer
          simulation / knowledge layer
```

## Repository

- `boot/` - Spit Fire and Jasper boot material.
- `include/` and `src/` - public interfaces and host-side C/C++ prototypes.
- `desktop/aurora/` - original Aurora Wayland/Vulkan compositor research.
- `userspace/aurora/` - enhanced Aurora Wayland userspace integration and build boundary.
- `network/spotnik/` - zero-copy networking research.
- `chimera_ii_c/` and `web/` - browser-backed host prototype.
- `tests/` - unit and smoke tests.
- `docs/` - architecture, research, provenance, plans and source-package references.
- `legacy/` - explicitly isolated legacy reference material.
- `demos/` - reserved for imported snapshots of external demo deployments.

## Build

Core build, independent of graphical host dependencies:

```bash
cmake -S . -B build -DAURORA_BUILD=OFF
cmake --build build
ctest --test-dir build --output-on-failure
```

Aurora userspace build, when Wayland development dependencies are installed:

```bash
cmake -S . -B build-aurora -DAURORA_BUILD=ON
cmake --build build-aurora
ctest --test-dir build-aurora --output-on-failure
```

See [`docs/AURORA_BUILD_RUN.md`](docs/AURORA_BUILD_RUN.md) and [`docs/superpowers/plans/2026-09-07-aurora-wayland-integration.md`](docs/superpowers/plans/2026-09-07-aurora-wayland-integration.md).

## Engineering status

RegisterN, R8192/C8192, Spit Fire, Jasper, Koronos, Spotnik, Kore, Aurora, Nucleus, Hive and CEF are research/prototype components. The 8192-bit processor is a virtual architecture target, not a claim of existing 8192-bit silicon. Aurora userspace is currently a dependency-gated foundation; its full wlroots backend, protocol handlers, rendering pipeline, and Kore device broker remain staged engineering work.

## Demo-source policy

The two live demo URLs are linked above. Their complete source has not been silently reconstructed from inaccessible/generated deployment output. When an export of either demo is supplied, the original snapshot should be preserved under `demos/` and then reviewed for dependencies, licenses, generated assets, and reusable source before integration into the main architecture.

## Consolidation

This repository is a consolidation of source packages, source blocks, specifications and research artifacts available in the associated ChatGPT project workspace. Historical binary documents are represented in the repository by extracted text where GitHub's text-content API permits direct publication; original packages remain available as the local project archive.

## License

See `LICENSE` and `THIRD_PARTY_LICENSES.md`. Third-party dependencies retain their own licenses.
