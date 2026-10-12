import json
import tempfile
import unittest
from pathlib import Path

from importlib.util import spec_from_file_location, module_from_spec

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "isa" / "tools" / "import_llvm_targets.py"
SPEC = spec_from_file_location("import_llvm_targets", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class LLVMTableGenImportTests(unittest.TestCase):
    def test_imports_real_instruction_records_with_provenance(self):
        document = {
            "!instanceof": {"Instruction": ["ADDrr", "SUBrr"]},
            "ADDrr": {"AsmString": "add $src, $dst", "Inst": "0b1010", "Uses": ["EFLAGS"]},
            "SUBrr": {"AsmString": "sub $src, $dst", "Inst": "0b1011", "Defs": ["EFLAGS"]},
            "NotAnInstruction": {"Comment": "ignore me"},
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x86.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            rows = MODULE.import_target(
                "x86-64", path, "https://example.invalid/llvm",
                "immutable-test-revision", "Apache-2.0 WITH LLVM-exception"
            )
        self.assertEqual([row["source_record"] for row in rows], ["ADDrr", "SUBrr"])
        self.assertEqual(rows[0]["mnemonic"], "add")
        self.assertEqual(rows[0]["effect_source_fields"]["Uses"], ["EFLAGS"])
        self.assertEqual(rows[0]["status"], "catalog-only")
        self.assertFalse(rows[0]["encoding_verified"])
        self.assertFalse(rows[0]["execution_implemented"])
        self.assertEqual(rows[0]["effects"]["registers_read"], "unknown")
        self.assertEqual(len(rows[0]["source_provenance"]["input_sha256"]), 64)

    def test_rejects_unrecognized_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text('{"!instanceof":{"Instruction":["I"]},"I":{"AsmString":"nop"}}')
            with self.assertRaises(ValueError):
                MODULE.import_target("mystery", path, "url", "rev", "license")

    def test_no_instruction_class_uses_cautious_record_fallback(self):
        document = {"NOP": {"AsmString": "nop"}, "Metadata": {"Comment": "skip"}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fallback.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            rows = MODULE.import_target("aarch64", path, "url", "rev", "license")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_record"], "NOP")


if __name__ == "__main__":
    unittest.main()
