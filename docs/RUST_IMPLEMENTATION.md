# Rust Implementation

`rust/ChimeraIIOS` is a separate Rust workspace mirroring core Chimera concepts: architecture identity, RegisterN-style wide integers, research ISA metadata, quantum state primitives, multidimensional vectors and a CLI.

## Current Rust research runtime

- `chm-core`: architecture/capability profiles and runtime modes.
- `chm-register`: wide-register research types.
- `chm-isa`: classical and quantum research operation descriptors.
- `chm-quantum`: dependency-free complex state-vector simulation with X/Y/Z/H/phase gates, Bell-state fixture and normalization tests.
- `chm-multidim`: generic vector norms, inner products, affine observer transforms, normalization and perception overlays.
- `chm-cli`: command-line integration boundary.

The quantum implementation follows mathematical state-vector semantics while remaining independent of cloud SDKs. External QPU/GPU adapters can be added behind capability traits without making them mandatory for local execution.

## Multidimensional model

The Rust multidimensional crate implements the geometry/perspective separation documented in `docs/MULTIDIMENSIONAL_PERSPECTIVE.md`. The 128D profile is an experimental semantic representation rather than a physical claim.

## Build

Install stable Rust and run:

```text
cd rust/ChimeraIIOS
cargo test --workspace
```

The repository CI workflow performs this test on Ubuntu. The current chat execution environment did not expose Cargo, so a local model-side Rust compilation result is not claimed here.

## Kernel boundary

The current edition is a safe user-space/runtime research layer. Bootloader/kernel integration remains a separate target requiring freestanding `no_std`, linker scripts, ABI validation and hardware testing. Rust should not silently replace the existing C/C++ boot path until those validation requirements are satisfied.
