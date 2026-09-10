# Chimera II OS — C# / .NET

The C# implementation is the managed application/tooling layer for Chimera II OS. It mirrors the stable cross-language contracts used by Python, Node.js, Java and C++ without replacing the native kernel.

Targets:
- `net8.0` — LTS baseline
- `net9.0` — STS compatibility target
- `net10.0` — current LTS target

Desktop targets use Windows Forms/WPF where appropriate; service and contract code remains platform-neutral. Native/boot-critical code remains C/C++/assembly.

Security boundary: this layer supports operator-owned wallet restore/verification, public blockchain observation, deterministic test vectors and research workloads. It does not implement address-to-private-key recovery, seed guessing or unauthorized credential access.
