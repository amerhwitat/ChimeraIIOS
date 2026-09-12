import importlib.util
from pathlib import Path

root = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("chm_neural", root / "python" / "chimera_neural.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_reasoning_confidence_is_bounded():
    r = mod.reason([mod.Evidence(.9, 2), mod.Evidence(.8, 1)])
    assert 0 <= r.score <= 1
    assert 0 <= r.confidence <= 1

def test_perception_overlay():
    assert mod.perception([2, 4], [0.5, 1]) == [1, 4]
