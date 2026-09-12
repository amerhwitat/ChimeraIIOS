# Quantum Source Provenance

Chimera II OS uses clean-room implementations and stable adapter boundaries. Third-party source is not copied wholesale.

| Project | Use | License/source note |
|---|---|---|
| Qiskit | circuit/operator and C/Python interoperability research | Apache-2.0 project; use public APIs/documentation |
| Cirq | Python circuit/simulator interoperability | Apache-2.0 project |
| PennyLane | QML/QChem/gradient research adapters | Apache-2.0 project |
| NVIDIA CUDA-Q | hybrid C++/Python CPU/GPU/QPU adapter research | inspect repository license files |
| NVIDIA cuQuantum | optional high-performance simulator backend | mixed licensing; inspect component headers/LICENSE files |

Versions must be pinned before packaging a release.
