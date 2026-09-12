# Quantum Source Provenance

Chimera II OS was informed by public quantum software projects but uses clean-room implementations. Third-party source is not copied wholesale.

## Research sources consulted

- Qiskit: https://github.com/Qiskit/qiskit — circuit/primitives/provider architecture.
- Cirq: https://github.com/quantumlib/Cirq — circuit construction and simulation abstractions.
- PennyLane: https://github.com/PennyLaneAI/pennylane — hybrid quantum-classical workflows and differentiation concepts.
- NVIDIA CUDA-Q: https://github.com/NVIDIA/cuda-quantum — heterogeneous CPU/GPU/QPU execution architecture.
- NVIDIA cuQuantum: https://github.com/NVIDIA/cuQuantum — accelerated quantum simulation ecosystem.
- qsim: https://github.com/quantumlib/qsim — C++ simulation and Python binding architecture.
- Spinoza: https://github.com/QuState/spinoza — pure-Rust high-performance state-vector simulation patterns.

These projects are reference ecosystems, not vendored source. Their current repository licenses and individual file headers remain authoritative. In particular, CUDA-Q/cuQuantum components require license inspection before any direct redistribution, while PennyLane documents Apache-2.0 licensing and Cirq documents Apache-2.0 licensing. 

## Chimera implementation policy

1. Reimplement algorithms from mathematical specifications rather than copying implementation bodies.
2. Preserve upstream attribution and URLs in this document when an architecture is materially informed by an upstream project.
3. Keep provider credentials, cloud endpoints and hardware-specific secrets outside the repository.
4. Local CPU simulation must remain usable with no external service.
5. Optional provider/GPU integrations must be capability-gated.
6. Third-party dependencies retain their own licenses; Chimera source remains GPLv3-or-later unless a subcomponent explicitly states otherwise.

## Mathematical boundary

State-vector evolution, unitary gates, Fourier transforms and Born probabilities are established mathematical/physics concepts. The Chimera 128D perspective layer is an experimental computational abstraction and must not be presented as established physical theory.
