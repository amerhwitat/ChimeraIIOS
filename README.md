# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research and engineering prototype. This repository separates host-emulated components from future bare-metal firmware, kernel, driver, FPGA, and silicon work.

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
- `desktop/aurora/` - Aurora Wayland/Vulkan compositor research.
- `network/spotnik/` - zero-copy networking research.
- `chimera_ii_c/` and `web/` - browser-backed host prototype.
- `tests/` - unit and smoke tests.
- `docs/` - architecture, research, provenance, plans and source-package references.
- `legacy/` - explicitly isolated legacy reference material.

## Build

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Engineering status

RegisterN, R8192/C8192, Spit Fire, Jasper, Koronos, Spotnik, Kore, Aurora, Nucleus, Hive and CEF are research/prototype components. The 8192-bit processor is a virtual architecture target, not a claim of existing 8192-bit silicon.

## Consolidation

This repository is a consolidation of source packages, source blocks, specifications and research artifacts available in the associated ChatGPT project workspace. Historical binary documents are represented in the repository by extracted text where GitHub's text-content API permits direct publication; original packages remain available as the local project archive.

## License

See `LICENSE` and `THIRD_PARTY_LICENSES.md`. Third-party dependencies retain their own licenses.
