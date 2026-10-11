import json
import pathlib
import tempfile
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "isa"))
from chimera_isa_mapper import build_mapping, load_database, append_jsonl


class IsaMapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = load_database(ROOT / "isa" / "isa_database.json")

    def test_unknown_architecture_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown source architecture"):
            build_mapping(self.db, "made-up-isa", "ADD")

    def test_candidate_inventory_not_execution_claim(self):
        result = build_mapping(self.db, "riscv64", "ADD", "x1,x2,x3")
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["decision"], "candidate-list-only")
        self.assertGreaterEqual(len(result["targets"]), 100)
        self.assertEqual({x["architecture"] for x in result["native_chimera_targets"]},
                         {"chimera-c8192", "chimera-r8192"})

    def test_exact_form_candidate_is_evidence_based(self):
        result = build_mapping(self.db, "riscv64", "ADD")
        riscv = next(x for x in result["targets"] if x["architecture"] == "riscv64")
        self.assertEqual(riscv["status"], "verified-form-candidate")
        self.assertTrue(riscv["forms"])

    def test_jsonl_retains_negative_candidates(self):
        result = build_mapping(self.db, "riscv64", "NOT_A_REAL_MNEMONIC")
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "dataset.jsonl"
            append_jsonl(target, result)
            row = json.loads(target.read_text(encoding="utf-8"))
            self.assertGreater(len(row["targets"]), 100)
            self.assertTrue(any(x["status"] == "no-exact-form" for x in row["targets"]))
            self.assertFalse(row["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
