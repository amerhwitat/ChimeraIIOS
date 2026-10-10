#!/usr/bin/env python3
"""Focused tests for the Chimera ISA candidate reference interpreter."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("chimera_isa_candidate",ROOT/"tools/isa/chimera_isa_candidate.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class CandidateRuntimeTests(unittest.TestCase):
    def test_candidate_inventory_covers_every_architecture(self):
        db=MOD.load_db()
        rows=MOD.build_candidates(db)
        self.assertGreaterEqual(len(rows),len(db["architectures"]))
        self.assertEqual({a[0] for a in db["architectures"]},{r["architecture"] for r in rows})

    def test_supported_add_mapping(self):
        db=MOD.load_db()
        candidates=MOD.build_candidates(db)
        row=next(r for r in candidates if r["architecture"]=="riscv64" and r.get("mnemonic")=="ADD")
        self.assertEqual(row["semantic_operation"],"add")
        self.assertEqual(row["native_mode"]["status"],"reference-micro-op")

    def test_unsupported_candidate_is_not_claimed_executable(self):
        db=MOD.load_db()
        rows=MOD.build_candidates(db)
        row=next(r for r in rows if r["architecture"]=="riscv64" and r.get("mnemonic")=="FENCE")
        self.assertEqual(row["compatibility_mode"]["status"],"unsupported")

    def test_8192_bit_mask(self):
        value=(1<<8192)+7
        self.assertEqual(value & ((1<<8192)-1),7)

    def test_formats_include_project_binary(self):
        self.assertIn("ncb",MOD.FORMATS)

if __name__=="__main__": unittest.main()
