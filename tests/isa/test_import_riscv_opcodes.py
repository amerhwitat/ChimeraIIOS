import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "isa" / "import_riscv_opcodes.py"
SPEC = importlib.util.spec_from_file_location("import_riscv_opcodes", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RiscVOpcodeImportTests(unittest.TestCase):
    def test_source_revision_is_pinned_in_record(self):
        revision = "5783cf3bea312a48d28e3e2c8a2fcb55603e4bed"
        rows = MODULE.parse_file(
            "add 6..0=0x33 11..7=1\n", "extensions/rv_i",
            "a" * 64, revision
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_revision"], revision)
        self.assertIn(revision, rows[0]["source_ref"])
        self.assertEqual(rows[0]["execution_status"], "not-implemented")
        self.assertEqual(rows[0]["memory_effects"], "unknown")

    def test_cached_import_must_match_pinned_revision(self):
        import json, tempfile
        revision=MODULE.DEFAULT_REVISION
        valid={"schema":"CHM-ISA-SOURCED-IMPORT-1","record_count":1,
               "instructions":[{"source_revision":revision}]}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"cached.json"
            path.write_text(json.dumps(valid),encoding="utf-8")
            self.assertTrue(MODULE.cached_import_is_valid(path,revision))
            self.assertFalse(MODULE.cached_import_is_valid(path,"0"*40))
            path.write_text(json.dumps({"schema":"wrong","record_count":1,"instructions":valid["instructions"]}),encoding="utf-8")
            self.assertFalse(MODULE.cached_import_is_valid(path,revision))

    def test_unfixed_source_revision_is_not_the_default(self):
        self.assertRegex(MODULE.DEFAULT_REVISION, r"^[0-9a-f]{40}$")
        self.assertIn("{revision}", MODULE.API_TREE)


if __name__ == "__main__":
    unittest.main()
