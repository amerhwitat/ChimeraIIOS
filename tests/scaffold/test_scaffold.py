from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "scaffold"))
from chimera_scaffold import scaffold

def test_scaffold_is_non_destructive(tmp_path):
    first = scaffold(tmp_path, ["desktop"])
    assert first["created"]
    marker = tmp_path / "desktop" / "kernel" / ".chimera-scaffold"
    before = marker.read_text()
    second = scaffold(tmp_path, ["desktop"])
    assert second["created"] == []
    assert marker.read_text() == before
