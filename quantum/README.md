# Chimera II OS Quantum Computing

Portable research quantum-computing subsystem for Chimera II OS. The CPU simulator is the baseline; optional adapters can target Qiskit, Cirq, PennyLane, NVIDIA CUDA-Q and cuQuantum.

## Included
- state-vector primitives and Bell/QFT reference implementations;
- versioned JSON circuit/result schemas;
- C/C++ ABI boundary for Koronos/RegisterN integration;
- Python reference implementation and optional external-SDK adapters;
- Rust implementation in `../rust/ChimeraIIOS`;
- research ISA metadata (`QINIT`, `QGATE`, `QCONTROL`, `QMEASURE`, `QTENSOR`, `QSYNC`).

These are research/educational simulators, not claims of fault-tolerant quantum hardware.
