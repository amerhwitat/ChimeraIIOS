# Chimera II OS Polyglot Native SDK

The SDK is the common developer layer for native and managed applications. It preserves the existing C/C++, C#, Objective-C, Java/JVM and Python interfaces and adds first-class Rust plus toolchain integration for Zig, Go, Fortran and Swift.

## Core modules

- `chimera_kernel` — syscalls, processes, IPC and scheduler-facing APIs
- `chimera_fs` — filesystem and TensorFS interfaces
- `chimera_net` — networking and zero-copy packet interfaces
- `chimera_graphics` — Aurora/Wayland/graphics interfaces
- `chimera_tensor` — tensor/vector/128D/large-width operations
- `chimera_nbit` — arbitrary logical N-bit arithmetic
- `chimera_runtime` — common runtime metadata
- `chimera_ffi` — stable C ABI boundary

## Language bindings

Python uses the `chimera` package and the `chimera-python` driver. Native extensions can use CPython's Limited/Stable ABI (`abi3`/`abi3t`) when cross-version compatibility is required.

Rust uses `sdk/rust/chimera-runtime`; C-compatible interfaces use `extern "C"` and `#[repr(C)]` at the ABI boundary, with Cargo retaining responsibility for dependencies and builds.

Java uses `sdk/java`; applications can reach native Chimera libraries through JNI or the Foreign Function & Memory API. Java remains portable bytecode while native code remains in the Chimera SDK.

C/C++ continue to use `chimera-ncc`, CMake, LLVM/Clang or GCC and the installed Chimera libraries.

Zig, Go, Fortran and Swift are exposed through toolchain drivers and the common C ABI where the corresponding upstream compiler is installed.

## Ecosystem libraries

The OS/package layer may integrate established libraries such as Python NumPy/SciPy/PyTorch/JAX, Rust crates, Java Maven/Gradle dependencies and C/C++ pkg-config/CMake packages when a target-compatible build and license are available. These projects are not silently vendored into the Chimera source tree; package metadata records provenance, license, ABI and target compatibility.

See `tools/chimera-toolchain/languages.json` and `tools/chimera-toolchain/README.md` for the machine-readable and human-readable integration contracts.
