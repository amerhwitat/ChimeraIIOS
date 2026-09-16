import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "repair"))
from chimera_repair import diagnose

def test_diagnose_missing_build(tmp_path):
    report = diagnose(tmp_path)
    assert report["build_dir_exists"] is False
    assert report["cmake_cache_exists"] is False
    assert "configure" in report["recommended_actions"]
