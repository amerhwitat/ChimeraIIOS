# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop/mobile, networking, data and intelligent-computing ecosystem.**

> Status: public research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, mobile-hardware and silicon targets.

## Cross-language crypto/AI solution

Chimera II now participates in the unified research implementation matrix:

| Language | Role |
|---|---|
| Python | Reference research, ML/RL and data-processing layer |
| Node.js | Web/integration runtime under `src/node/` |
| Java | Koronos semantic/JVM interoperability layer |
| C++ | Native kernel/ISA/desktop implementation layer |

All four tracks use deterministic JSON/JSONL contracts, public/synthetic vectors, provenance metadata and C8192/R8192 telemetry boundaries. The Node.js integration does not replace Koronos, Spit Fire, Jasper, Spotnik, Aurora or native drivers.

## Architecture baseline

```text
CHIMERA II OS
  |
  +-- MACHINE PLANE: R8192 / C8192 / RegisterN / Tensor / Vector
  +-- COGNITIVE PLANE: Koronos 128D / knowledge / reasoning research
  +-- WORLD PLANE: network / GPU / files / sensors / storage / UI
  |
  +-- KORONOS: ISA / MM / scheduler / IRQ / VFS / IPC / networking
  |
  +-- AURORA / GPU / CEF / WEB
```

The 8192-bit processor is an architectural/emulation research target, not a claim of existing 8192-bit silicon. Physical performance and energy claims require measured implementations.

## Crypto/AI integration

`docs/CRYPTO_AI_SCANNER_INTEGRATION.md` defines public blockchain observation, normalized storage, AI/RL workloads and deterministic C8192/R8192 vectors. Wallet operations require operator-controlled wallets or externally signed transactions. Private-key cracking, address-targeted brute force, seed guessing and unauthorized credential access are excluded.

## Aurora

Aurora is the shared native Wayland/Web desktop surface with glass panels, bilingual English/Arabic UI, system widgets and mobile extensions. Native rendering remains separated from the browser implementation.

## Toolchain and IDE

The project integrates GCC/G++, Clang, CMake/Ninja/Make/Meson, GDB/CDB/Chimera debugger contracts and Chimera CISC/RISC/native/emulator targets.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/installer/test_installer_plan.py
```

For the web layer, see `src/node/` and the corresponding documentation.

## Research/provenance

See `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`, `docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md`, `docs/CI_CD_PUBLIC_RESEARCH_OS_PLAN.md`, `docs/AUTHOR_BIBLIOGRAPHY_AMER_HWITAT.md` and the language-specific READMEs.