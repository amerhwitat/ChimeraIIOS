# Quantum Source Provenance

Chimera II OS was informed by public quantum software projects but uses clean-room implementations. Third-party source is not copied wholesale.

## Official research sources

- Qiskit: https://github.com/Qiskit/qiskit
- Cirq: https://github.com/quantumlib/Cirq
- PennyLane: https://github.com/PennyLaneAI/pennylane
- NVIDIA CUDA-Q: https://github.com/NVIDIA/cuda-quantum
- NVIDIA CUDA-Q documentation: https://nvidia.github.io/cuda-quantum/latest/
- NVIDIA cuQuantum: https://github.com/NVIDIA/cuQuantum

Qiskit is Apache-2.0; Cirq and PennyLane are Apache-2.0 projects; CUDA-Q and cuQuantum require inspection of their repository license files and component headers before redistribution. cuQuantum explicitly documents mixed licensing for some components.

Recommended adapter policy: pin versions, preserve source URLs, retain license notices, keep provider credentials outside the repository, and make external execution opt-in.
