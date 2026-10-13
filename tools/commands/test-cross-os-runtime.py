#!/usr/bin/env python3
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "chimera-run"
MANIFEST = ROOT / "os-command-runtime.json"
class RuntimeRegistryTests(unittest.TestCase):
    def test_manifest_schema_and_policy(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("chimera-native", data["providers"])
        self.assertTrue(data["policy"]["do_not_download_or_execute_untrusted_binaries_automatically"])
        for provider in data["providers"].values():
            self.assertTrue(provider["commands"])
            self.assertIn("mode", provider)
    def test_list_commands(self):
        p = subprocess.run([sys.executable, str(RUNNER), "--list"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("chimera-run", p.stdout)
        self.assertIn("powershell", p.stdout)
    def test_unknown_command_is_not_found(self):
        p = subprocess.run([sys.executable, str(RUNNER), "definitely-not-a-real-chimera-command-7d9"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 127)
        self.assertIn("command not found", p.stderr)
    def test_mode_validation(self):
        p = subprocess.run([sys.executable, str(RUNNER), "--mode", "mystery", "echo"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("mode must be", p.stderr)
if __name__ == "__main__":
    unittest.main()
