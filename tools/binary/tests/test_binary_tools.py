import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCANNER = ROOT / "tools/binary/scan-binaries.py"
RUNNER = ROOT / "tools/binary/run-compat.py"

class BinaryToolsTests(unittest.TestCase):
    def test_recursive_scan_detects_elf_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            sample = bytearray(64)
            sample[:4] = b"\x7fELF"
            sample[4:8] = bytes([2, 1, 1, 0])
            sample[18:20] = (62).to_bytes(2, "little")
            (root / "nested").mkdir()
            (root / "nested" / "sample.bin").write_bytes(sample)
            report = root / "report.json"
            subprocess.run([sys.executable, str(SCANNER), str(root), "--json", str(report)], check=True)
            data = json.loads(report.read_text())
            self.assertEqual(data["files_scanned"], 1)
            self.assertEqual(data["executables"][0]["format"], "ELF")
            self.assertEqual(data["executables"][0]["architecture"], "x86_64")
            self.assertEqual(len(data["executables"][0]["sha256"]), 64)

    def test_compatibility_runner_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample = pathlib.Path(tmp) / "native.elf"
            data = bytearray(64)
            data[:4] = b"\x7fELF"; data[4:8] = bytes([2,1,1,0])
            data[18:20] = (62).to_bytes(2,"little")
            sample.write_bytes(data)
            result = subprocess.run([sys.executable, str(RUNNER), str(sample)],
                                    check=True, capture_output=True, text=True)
            self.assertIn("Dry run only", result.stdout)
            self.assertIn("Selected runtime:", result.stdout)

if __name__ == "__main__":
    unittest.main()
