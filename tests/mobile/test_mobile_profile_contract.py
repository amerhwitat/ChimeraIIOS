#!/usr/bin/env python3
"""Regression tests for fail-closed mobile device profiles and flash behavior."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("chimera_mobile_build", ROOT / "tools/mobile/chimera-mobile-build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class MobileProfileTests(unittest.TestCase):
    def test_all_generic_profiles_are_reference_only(self):
        for path in sorted((ROOT / "mobile/device-profiles").glob("*.json")):
            if path.name == "README.md":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data.get("support_status"), "reference-only", path.name)
            self.assertEqual(data.get("match"), {}, path.name)

    def test_reference_profile_never_matches_a_real_device(self):
        target = {"architecture": "aarch64", "properties": {
            "manufacturer": "Example", "model": "Example Phone", "device": "example",
            "product": "example", "board": "example", "platform": "example"
        }}
        with self.assertRaisesRegex(SystemExit, "No hardware-validated exact-device profile"):
            builder.load(target)

    def test_build_rejects_unvalidated_profile_before_packaging(self):
        profile = json.loads((ROOT / "mobile/device-profiles/reference-aarch64.json").read_text())
        with self.assertRaisesRegex(SystemExit, "not hardware-validated"):
            builder.build({"architecture": "aarch64", "properties": {}}, profile,
                          ROOT / "mobile/device-profiles/reference-aarch64.json")

    def test_profile_validator_accepts_reference_only_but_not_unverified_as_supported(self):
        validator = ROOT / "mobile/build/validate-profile.py"
        profile = ROOT / "mobile/device-profiles/reference-aarch64.json"
        q = subprocess.run(["python3", str(validator), str(profile)], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(q.returncode, 0, q.stdout)
        self.assertIn("reference-only", q.stdout)

    def test_generic_partition_flash_is_disabled(self):
        cli = ROOT / "tools/mobile/chimera-mobile-flash.sh"
        q = subprocess.run(["bash", str(cli), "generic-flash"], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertNotEqual(q.returncode, 0)
        self.assertIn("generic-flash is disabled", q.stdout)

    def test_fastboot_helper_rejects_reference_profile_before_device_access(self):
        helper = ROOT / "tools/mobile/chimera-mobile-fastboot.py"
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "build.json"
            report.write_text(json.dumps({
                "target": {"serial": "not-a-real-device", "properties": {}},
                "profile": {"support_status": "reference-only"}
            }), encoding="utf-8")
            q = subprocess.run(["python3", str(helper), str(report)], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertNotEqual(q.returncode, 0)
            self.assertIn("not hardware-validated", q.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
