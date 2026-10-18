import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MATRIX = ROOT / "architecture" / "support-matrix.json"


class SupportMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_schema_and_unique_target_ids(self):
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(self.data["policy"], "evidence-gated")
        ids = [target["id"] for target in self.data["targets"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"native", "virtual-machine", "instruction-emulation", "compatibility-layer"} <= set(self.data["execution_modes"]))

    def test_every_target_has_explicit_evidence_and_status(self):
        for target in self.data["targets"]:
            with self.subTest(target=target["id"]):
                self.assertIn(target["family"], {"CISC", "RISC"})
                self.assertIn("native_kernel", target)
                self.assertIn("qemu", target)
                self.assertIn("userspace", target)
                self.assertIsInstance(target["release_supported"], bool)
                self.assertTrue(target["evidence_required"])
                if target["release_supported"]:
                    self.assertIn("evidence", target, "supported targets must link verifiable acceptance evidence")

    def test_unaccepted_targets_are_not_marked_supported(self):
        for target in self.data["targets"]:
            if target["userspace"] == "not-accepted" or "not-accepted" in target["native_kernel"]:
                self.assertFalse(target["release_supported"], target["id"])

    def test_mobile_requires_device_specific_acceptance(self):
        mobile = next(t for t in self.data["targets"] if t["id"] == "aarch64-mobile-device")
        for required in ("display-touch", "wifi-cellular", "power-management", "verified-update", "recovery"):
            self.assertIn(required, mobile["evidence_required"])


if __name__ == "__main__":
    unittest.main()
