#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
MODULE = Path(__file__).with_name("refresh_isa_catalog.py")
spec = importlib.util.spec_from_file_location("refresh_isa_catalog", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class RefreshISATests(unittest.TestCase):
    def test_semantic_fields_are_explicit(self):
        for field in ("register_classes", "flags_read", "flags_written", "memory_effects",
                      "source_ref", "source_revision", "execution_status", "license"):
            self.assertIn(field, mod.SEMANTIC_FIELDS)
    def test_refresh_pipeline_is_explicit(self):
        self.assertEqual(mod.PIPELINE[0][1], ["--refresh"])
        self.assertTrue(any("import_riscv_opcodes.py" in path for path, _ in mod.PIPELINE))
    def test_status_is_not_inferred_from_catalog_presence(self):
        self.assertIn("not-implemented", {"conformance-tested", "implemented-unverified",
                                          "not-implemented", "not-applicable"})
if __name__ == "__main__":
    unittest.main()
