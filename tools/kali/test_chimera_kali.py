#!/usr/bin/env python3
"""Contract tests for the opt-in Kali-compatible package frontend."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("chimera-kali")


class KaliFrontendContract(unittest.TestCase):
    def run_cli(self, *args, opt_in):
        env = os.environ.copy()
        env["CHIMERA_KALI_OPT_IN"] = str(opt_in)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_list_exposes_core_modes_and_categories_without_enabling_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("list", opt_in=Path(tmp) / "disabled")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("kali-linux-core", result.stdout)
        self.assertIn("kali-linux-everything", result.stdout)
        self.assertIn("kali-tools-information-gathering", result.stdout)
        self.assertIn("no source is enabled automatically", result.stdout.lower())

    def test_install_fails_closed_without_explicit_repository_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("install", "top10", opt_in=Path(tmp) / "disabled")
        self.assertEqual(result.returncode, 4)
        self.assertIn("blocked", result.stderr.lower())

    def test_install_rejects_invalid_package_identifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            opt_in = Path(tmp) / "opt-in"
            opt_in.write_text("enabled=true\n", encoding="utf-8")
            result = self.run_cli("install", "../../shell", opt_in=opt_in)
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid package", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
