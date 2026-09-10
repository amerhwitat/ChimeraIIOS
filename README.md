# Chimera II OS

**Research-grade modular operating-system, virtual-processor, mobile, desktop, networking, data, and intelligent-computing ecosystem.**

> **Status:** public research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, mobile-hardware and silicon targets.
>
> **Author / research lead:** Amer Hwitat

## Public Research OS

Chimera II OS is published as an open research project with Git as the portable source-history layer and GitHub as the current canonical public forge. A forge-federation plan documents GitLab, Codeberg/Forgejo and SourceHut as secondary mirror targets when user-controlled repositories are created.

- [Open-source publication & federation](docs/OPEN_SOURCE_RESEARCH_OS_PUBLICATION.md)
- [Source-code management federation](docs/SOURCE_CODE_MANAGEMENT_FEDERATION.md)
- [Amer Hwitat bibliography](docs/AUTHOR_BIBLIOGRAPHY_AMER_HWITAT.md)
- [Library research archive index](docs/LIBRARY_RESEARCH_ARCHIVE_INDEX.md)
- [Public CI/CD plan](docs/CI_CD_PUBLIC_RESEARCH_OS_PLAN.md)
- [Crypto upstreams and provenance](docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md)
- [Research OS web landing page](web/research-os.html)
- [Search sitemap](web/sitemap.xml)

### Related public repositories

- [CPU4096](https://github.com/amerhwitat/CPU4096)
- [CPU4096Simulator](https://github.com/amerhwitat/CPU4096Simulator)
- [general / mobile integration](https://github.com/amerhwitat/general)
- [nlp](https://github.com/amerhwitat/nlp)
- [PDFreaderPY](https://github.com/amerhwitat/PDFreaderPY)
- [bruteforce](https://github.com/amerhwitat/bruteforce)
- [keygen](https://github.com/amerhwitat/keygen)
- [eth-key-check](https://github.com/amerhwitat/eth-key-check)
- [BizX](https://github.com/amerhwitat/BizX)
- [BizXtreme](https://github.com/amerhwitat/BizXtreme)
- [test](https://github.com/amerhwitat/test)
- [amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io)

The current GitHub inventory includes one private repository, `VanG`; its visibility must be changed by the account owner before it can honestly be described as public or mirrored. No private source is copied into the public Chimera research tree.

## Search-engine discoverability

The Web publication includes `robots.txt`, `sitemap.xml`, descriptive metadata, stable internal links, the public research landing page and the repository bibliography. Search engines decide when and how to crawl/index public pages; the project can improve discoverability but cannot guarantee ranking or indexing.

## Aurora Wayland Glass Desktop

Aurora is the shared glass desktop surface for native Wayland and the browser Web UI. The canonical visual language is a scenic mountain/lake background, translucent frosted-glass panels, rounded window chrome, blue/purple accents, top bar, docks and system widgets.

The native stack remains **DRM/KMS → Mesa/Vulkan/OpenGL → Aurora compositor → Wayland clients**, with software rendering fallback. The Web implementation mirrors the surface/window model using managed application windows and constrained embedded pages.

## Aurora Mobile Edition

The Mobile Edition extends Aurora into a portrait-first interface with mobile interaction patterns, bilingual English/Arabic labels, telemetry cards, quick actions, application grid, terminal, files, browser, store, security and system services.

- `web/mobile-landing.svg` — repository-hosted Aurora-inspired mobile visual.
- `mobile/` — mobile runtime and package ecosystem.
- `docs/MOBILE_UNIVERSAL_PACKAGING_ARCHITECTURE.md` — package/target architecture.

The Library mobile architecture separates Mobile UI, application API, CPU/GPU/NPU/DSP, Chimera HAL and microkernel/V-Cores.

## Architecture baseline

The repository follows the Chimera II subsystem order: Spit Fire/Jasper boot, Koronos kernel, RegisterN, Spotnik networking, VFS/TensorFS/Nucleus/Hive data fabric, Aurora graphics, CEF services, security/CI, ISA tooling and QEMU-oriented tests.

```text
                       CHIMERA II OS
                              |
       +----------------------+----------------------+
       |                      |                      |
  MACHINE PLANE         COGNITIVE PLANE         WORLD PLANE
  R8192 / C8192         128D State             Network / GPU
  RegisterN             Knowledge              Files / Sensors
  Tensor / Vector       Reasoning              Storage / UI
       |                      |                      |
       +----------------------+----------------------+
                              |
                       KORONOS KERNEL
                              |
      ISA / MM / SCHED / IRQ / VFS / IPC / NET
                              |
                   AURORA / GPU / CEF / WEB
```

The 8192-bit processor remains an architectural/emulation research target, not a claim of existing 8192-bit silicon. The research specification explicitly separates architectural register width, instruction encoding width, execution lanes, issue width and memory bandwidth.

## Linux commands, terminal and source integration

The project maintains a unified Linux/Unix/Windows command catalog and Aurora terminal. Upstream code is tracked by provenance and license; unrelated upstream repositories are not collapsed into an opaque code dump.

## Toolchain and IDE

Aurora Code IDE supports GCC/G++, Clang/Clang++, MSVC/clang-cl adapters, CMake/Ninja/Make/Meson, GDB/CDB/Chimera debugger contracts and Chimera CISC/RISC/Native/Emulator targets.

## Mobile universal package ecosystem

The Mobile Edition contains the Package Fabric and adapters for Debian/dpkg/apt/apt-get/aptitude, RPM/DNF/YUM, pacman, apk, Nix, Flatpak, Snap, AppImage, Git/GitHub and Android/Swift-oriented target boundaries. `.deb` packages are permitted only through the transactional/signature/sandbox policy.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/installer/test_installer_plan.py
python3 tests/cognition/test_chimera_rnn.py
```

Web explorer:

```bash
python3 -m http.server 8080 --directory web
```

## CI/CD and releases

GitHub Actions is the canonical CI layer. The release pipeline is designed around license/provenance checks, static analysis, multi-architecture builds, ISA conformance, package tests, QEMU boot tests, Web UI tests, documentation/link/sitemap validation, SBOM/license scanning, checksums and signed release metadata.

See [docs/CI_CD_PUBLIC_RESEARCH_OS_PLAN.md](docs/CI_CD_PUBLIC_RESEARCH_OS_PLAN.md).

## Research bibliography and provenance

See [docs/AUTHOR_BIBLIOGRAPHY_AMER_HWITAT.md](docs/AUTHOR_BIBLIOGRAPHY_AMER_HWITAT.md), [docs/LIBRARY_RESEARCH_ARCHIVE_INDEX.md](docs/LIBRARY_RESEARCH_ARCHIVE_INDEX.md), and [docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md](docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md). The Library corpus includes the comprehensive redesign report, mobile/robotics architecture, low-level specification, developer guide, Web Runtime research, Linux/retro research and Aurora visual references.

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
