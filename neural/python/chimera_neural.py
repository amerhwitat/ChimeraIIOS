from dataclasses import dataclass
from math import sqrt
from typing import Sequence

@dataclass(frozen=True)
class Evidence:
    value: float
    weight: float = 1.0

@dataclass(frozen=True)
class Response:
    score: float
    confidence: float

def _c01(x: float) -> float:
    return max(0.0, min(1.0, x))

def reason(evidence: Sequence[Evidence]) -> Response:
    total = sum(max(0.0, e.weight) for e in evidence)
    if not total:
        return Response(0.0, 0.0)
    score = sum(_c01(e.value) * max(0.0, e.weight) for e in evidence) / total
    variance = sum(max(0.0, e.weight) * (_c01(e.value) - score) ** 2 for e in evidence) / total
    return Response(_c01(score), _c01(score * (1.0 - sqrt(variance))))

def perception(vector: Sequence[float], confidence: Sequence[float]) -> list[float]:
    return [x * (_c01(confidence[i]) if i < len(confidence) else 1.0) for i, x in enumerate(vector)]
