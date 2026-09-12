# Quantum Computing in Chimera II OS

Chimera II OS defines a portable quantum research layer with C/C++, C ABI, Python and Rust implementations plus language adapters. The CPU simulator is the fallback backend. Optional integrations can target Qiskit, Cirq, PennyLane, CUDA-Q and cuQuantum.

The model is hybrid: Koronos schedules classical work while quantum jobs are represented as validated circuit IR and dispatched to a local simulator or explicitly configured accelerator/provider.

No external provider is contacted by default.
