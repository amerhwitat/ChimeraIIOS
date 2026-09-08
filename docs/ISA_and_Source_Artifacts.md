# ISA Inventory, Source Artifacts, and Aurora → UE5 Integration

## Scope

Additive developer reference for Chimera II OS. This document catalogs representative RISC/CISC ISAs, defines the normalization strategy used by Chimera, and documents the optional Aurora Desktop Unreal Engine 5 integration.

> **Compatibility rule:** the Chimera core remains independent of Unreal Engine, Windows WDK, proprietary SDKs, and external ISA manuals.

## 1. ISA inventory

### RISC families

- **AArch64 / ARMv8+** — fixed 32-bit instruction encodings, SIMD/NEON and SVE; common in mobile, embedded and servers.
- **RISC-V** — open modular ISA with base integer ISA plus optional M/A/F/D/C/V and other extensions.
- **MIPS** — historically important load/store RISC family, especially in embedded/networking.
- **PowerPC / POWER** — server and embedded RISC family with vector extensions.
- **SPARC / OpenSPARC** — register-window RISC architecture used in servers and research.

### CISC families

- **x86-64 / AMD64 / Intel 64** — variable-length instruction encoding with extensive compatibility modes and mature privileged architecture.
- **x86 16/32-bit** — legacy modes relevant to boot, firmware and compatibility emulation.
- **VAX** — historical CISC family retained as an emulator/reference target.

### Specialized execution ISAs / IRs

- **NVIDIA PTX** — virtual ISA for NVIDIA GPU compilation and execution.
- **AMD GCN / ROCm ISA families** — GPU-oriented instruction and intermediate representations.
- **Chimera R8192/C8192** — research ISA concepts represented as lane-decomposed wide operations, not a claim of existing silicon.

## 2. Normalized Chimera ISA model

External instructions are decoded into a compact internal representation:

```text
bytes → decoder → normalized instruction → micro-ops → backend → retire
```

A normalized instruction records:

```cpp
struct Instruction {
    uint32_t opcode;
    uint8_t  width_class;
    uint8_t  operand_count;
    uint8_t  privilege;
    uint8_t  flags;
    uint64_t operands[4];
};
```

The actual implementation lives in `include/chimera/unified_isa.hpp` and `src/isa/unified_isa.cpp`. The catalog added by this change is metadata and test material; it does not replace the existing decoder.

## 3. Wide-register implementation guidance

An 8192-bit value is naturally represented as 128 little-endian 64-bit limbs. The same representation generalizes to N-bit widths:

```cpp
template <size_t Bits>
struct RegisterN {
    static_assert(Bits > 0 && Bits % 64 == 0);
    std::array<uint64_t, Bits / 64> limbs{};
};
```

For runtime widths, `chimera::runtime::WideInt` owns a contiguous limb vector. This keeps the existing N-bit API while allowing future widths without ABI changes.

## 4. Execution pipeline

```text
RISC / CISC / Chimera instruction
            ↓
       ISA decoder
            ↓
       normalized IR
            ↓
       micro-op expansion
            ↓
   ┌────────┼────────┐
   ↓        ↓        ↓
 Scalar   Vector   NativeWide
   │        │        │
   └────────┼────────┘
            ↓
           JIT
            ↓
    QuantumHybrid boundary
```

Every instruction family should have unit tests, malformed-input tests, and golden reference vectors before being marked stable.

## 5. Test-vector tooling

`tools/isa/isa_opcodes.csv` is a machine-readable Chimera catalog. `tools/isa/test_vector_generator.py` generates deterministic or randomized operands for emulator tests.

Example:

```bash
python3 tools/isa/test_vector_generator.py test_vectors.csv 500 --seed 42
```

The generator only produces test data. It does not assign semantics to external ISA instructions.

## 6. Portable assembly boundary

Architecture-specific optimization remains optional. The current repository uses an x86-64 pause/cycle-counter fast path under `src/arch/x86_64/` while the portable C++ implementation remains authoritative.

```asm
.section .text
.global chimera_cpu_pause
chimera_cpu_pause:
    pause
    ret
```

Other architecture backends should follow the same ABI and provide a portable fallback.

## 7. Aurora → Unreal Engine 5

The UE5 integration is intentionally isolated under `integrations/ue5/AuroraDesktop/`.

```text
UE5 application
      │
AuroraDesktop module
      ├── UMG / Slate
      ├── GPU materials
      └── optional Linux Wayland client
              │
              ↓
       native Aurora compositor
```

The plugin is a **Wayland client/front-end integration**, not a replacement for the native Aurora compositor. On Linux it may use `libwayland-client`; on other platforms the module builds without Wayland.

### Performance model

- Prefer Slate for frequently updated low-latency controls.
- Use UMG for composition and application-facing widgets.
- Downsample before expensive blur operations.
- Keep post-processing GPU-side.
- Reuse render targets and shader resources.
- Clamp browser/device pixel ratio in the web implementation.

### Frosted glass

The native Aurora implementation already contains the compositor-side compute blur. The UE5 plugin adds an equivalent material/custom-node strategy rather than duplicating native compositor code.

## 8. Provenance

The historical `W2K-ASM.txt` artifact is treated as research/provenance material. This repository does **not** reproduce Microsoft Confidential material from that document. The integration extracts general debugging/build lessons and uses newly written compatible code.

External ISA descriptions should link to their canonical specifications instead of vendoring copyrighted manuals.

## 9. Compatibility contract

These additions must not require:

- Unreal Engine for the core CMake build.
- Windows WDK for the core build.
- GPU hardware for unit tests.
- A quantum backend for `QuantumHybrid` to exist as an interface.

The existing Chimera API remains the stable integration point.
