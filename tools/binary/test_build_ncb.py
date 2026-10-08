import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/binary/build_ncb.py"
INSPECTOR = ROOT / "tools/binary/chimera_binary.py"
MANIFEST = ROOT / "tools/binary/manifest.example.json"


class NCBBuilderTests(unittest.TestCase):
    def test_example_manifest_builds_and_validates(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "sample.ncb"
            built = subprocess.run(
                [sys.executable, str(BUILDER), str(MANIFEST), str(output)],
                cwd=directory, text=True, capture_output=True, check=True,
            )
            self.assertEqual(json.loads(built.stdout)["word_bits"], 32)
            inspected = subprocess.run(
                [sys.executable, str(INSPECTOR), "--json", str(output)],
                cwd=directory, text=True, capture_output=True, check=True,
            )
            result = json.loads(inspected.stdout)
            self.assertEqual(result["format"], "Chimera NCB1")
            self.assertNotIn("validation_error", result)

    def test_missing_manifest_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(BUILDER), "manifest.json", "out.ncb"],
                cwd=directory, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("manifest is not a regular file", result.stderr)

    def test_inspector_rejects_directory_with_clear_message(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(INSPECTOR), directory],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("not a directory or special file", result.stderr)


if __name__ == "__main__":
    unittest.main()
