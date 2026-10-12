# Managed languages, .NET services, and Apple CPU targets

## C# and .NET

The SDK includes a minimal managed helper library and `tools/chimera-toolchain/chimera-csharp`, a command driver that delegates to the installed `dotnet` CLI. It supports project-level `build`, `test`, `run`, `publish`, `restore`, and `clean` commands. Roslyn, the .NET SDK, the CLR/JIT, base class libraries, native host dependencies, and a compatible target runtime must be installed separately.

The SDK project targets `net10.0`. This is a target-framework choice, not a promise that every Chimera image ships that runtime. Runtime services should be optional packages and system services; never download and execute an unpinned installer during ISO creation. Pin production SDK/runtime versions in the package lock/manifest and validate signatures and hashes.

A Linux-hosted .NET SDK can compile managed assemblies for supported targets, but compilation does not prove a native Chimera CLR exists. Until a CLR/JIT and BCL port is tested on Chimera, run managed applications only on an explicitly supported host runtime or a configured compatibility environment. Native N-bit support requires a defined managed ABI, GC integration, exception/unwind integration, thread model, syscall bridge and runtime tests; it is not obtained by setting a larger integer width.

## Intel Mac and Apple Silicon

`config/compatibility/apple-cpu-targets.json` defines separate x86-64 and AArch64 compiler target identities and required validation gates. Apple M-series CPUs implement the AArch64 ISA family, but their boot firmware, interrupt routing, power management, GPU, storage and other devices require platform-specific support. The Intel target likewise does not guarantee that a generic PC kernel boots on every Intel Mac.

Do not equate CPU compatibility with macOS application compatibility. Native macOS programs may depend on Mach-O loading, dyld, Apple SDK headers, frameworks, entitlements, signing and runtime behavior. Apple's Rosetta 2 is not bundled or reproduced by this target. Universal binaries require validated architecture slices and loader support.

## Language and package-manager policy

The language matrix and package-manager catalog are discovery registries. A catalog entry means that a tool can be detected or integrated, not that every version/target is already built or tested. Aurora should show each tool as **installed**, **available from configured provider**, **unsupported on this target**, or **not verified**.

When a preferred package provider is unavailable, the package UI may offer a compatible alternative provider after checking package identity, architecture, license, signature, dependency graph, permissions and isolation. It must not blindly retry the same package name across unrelated package managers. Snap requires snapd; Flatpak requires its runtime/portal setup; npm/Yarn/pnpm are language package managers and must not be treated as OS package managers. Ask for elevation before privileged changes.

## Completion gates

- Add a managed SDK build/test job where the matching .NET SDK is available.
- Verify the C# helper project and driver against a real SDK; absence of dotnet should be reported as skipped, not passed.
- Validate both target triples and object formats using cross-compilers.
- Keep boot acceptance separate from cross-compilation acceptance.
- Mark each foreign API/runtime feature by implemented, partial, planned and conformance-tested status.
