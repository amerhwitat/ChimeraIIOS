"""Clean-room Python reference adapter for the Chimera II OS quantum IR."""
from dataclasses import dataclass
from math import sqrt

@dataclass
class StateVector:
    qubits: int
    amplitudes: list[complex]

    @classmethod
    def zero(cls, qubits: int) -> "StateVector":
        if qubits < 1: raise ValueError("qubits must be positive")
        a = [0j] * (1 << qubits); a[0] = 1 + 0j
        return cls(qubits, a)

    def norm2(self) -> float:
        return sum(abs(x) ** 2 for x in self.amplitudes)

    def hadamard(self, target: int) -> None:
        if not 0 <= target < self.qubits: raise IndexError(target)
        bit = 1 << target; s = 1 / sqrt(2)
        for i in range(len(self.amplitudes)):
            if i & bit: continue
            j = i | bit; x, y = self.amplitudes[i], self.amplitudes[j]
            self.amplitudes[i], self.amplitudes[j] = s * (x + y), s * (x - y)
