import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "installer"))
from chimera_hardware_advisor import recommend


class HardwareAdvisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.db = json.loads((ROOT / "isa" / "isa_database.json").read_text(encoding="utf-8"))

    def test_unknown_facts_are_not_guessed(self):
        result = recommend(self.db, {"architecture": "mystery-cpu"})
        self.assertIsNone(result["hardware_facts"]["canonical_architecture"])
        self.assertTrue(result["unknowns_and_checks"])
        self.assertFalse(result["safety"]["automatic_partitioning"])

    def test_detected_architecture_is_not_support_claim(self):
        result = recommend(self.db, {"architecture": "x86_64", "ram_gib": 8, "storage_gib": 256, "firmware": "uefi"})
        self.assertEqual(result["hardware_facts"]["canonical_architecture"], "x86-64")
        self.assertIn("does not prove", result["isa_evidence"][0]["interpretation"])
        self.assertTrue(result["safety"]["recommendation_is_not_support_proof"])

    def test_developer_profile_is_opt_in(self):
        result = recommend(self.db, {"architecture": "aarch64", "use_case": "developer"})
        self.assertTrue(any(x["area"] == "optional-packages" for x in result["recommendations"]))

    def test_never_auto_partitions(self):
        result = recommend(self.db, {"architecture": "riscv64", "storage_gib": 512})
        self.assertFalse(result["safety"]["automatic_partitioning"])
        self.assertTrue(result["safety"]["require_user_confirmation_for_destructive_actions"])


if __name__ == "__main__":
    unittest.main()
