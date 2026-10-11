import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "nbit" / "select_mode.py"


class NBitModeSelectionTests(unittest.TestCase):
    def test_arbitrary_width_profile_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            run = subprocess.run(
                [sys.executable, str(TOOL), "--bits", "8193", "--backend", "chimera-virtual",
                 "--config", str(path)],
                check=True, capture_output=True, text=True,
            )
            profile = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(profile["selected_width_bits"], 8193)
            self.assertEqual(profile["backend"], "chimera-virtual")\n            self.assertEqual(profile["guest_isa"], "chimera-nbit")
            self.assertTrue(profile["validation_required_at_kernel_admission"])
            self.assertIn("physical CPU-native", run.stdout)

    def test_compatibility_personality_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            subprocess.run(
                [sys.executable, str(TOOL), "--bits", "32", "--backend", "compatibility",
                 "--compatibility", "linux", "--isa", "x86-32", "--config", str(path)],
                check=True, capture_output=True, text=True,
            )
            profile = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(profile["compatibility_personality"], "linux")\n            self.assertEqual(profile["guest_isa"], "x86-32")

    def test_invalid_width_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run(
                [sys.executable, str(TOOL), "--bits", "0", "--config", str(Path(tmp) / "p.json")],
                capture_output=True, text=True,
            )
            self.assertNotEqual(run.returncode, 0)


if __name__ == "__main__":
    unittest.main()
