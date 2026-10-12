#!/usr/bin/env python3
"""Regression tests for tools.isa.architecture_importers."""
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "architecture_importers.py"
SPEC = importlib.util.spec_from_file_location("architecture_importers", MODULE)
IMPORTERS = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(IMPORTERS)


def valid_row():
    return {
        "architecture": "aarch64",
        "mnemonic": "ADD",
        "form_id": "arm-example-add-form",
        "encoding": {
            "length_bits": 32, "value": 0x8b000000, "mask": 0xffe0fc00,
            "byte_order": "architecture-defined",
            "source_expression": "source-backed expression preserved verbatim"
        },
        "operands": [{"kind": "register"}, {"kind": "register"}, {"kind": "register"}],
        "provenance": {
            "source_url": "https://developer.arm.com/documentation/",
            "source_revision": "test-fixture-only",
            "source_license": "documented source terms reviewed separately",
            "retrieved_sha256": "sha256:fixture"
        },
        "effects": {
            "registers_read": ["Rn", "Rm"], "registers_written": ["Rd"],
            "flags_read": [], "flags_written": [], "memory_read": [],
            "memory_written": [], "exceptions": [], "privilege": ["all"],
            "extensions": ["A64"], "endianness": "architecture-defined"
        },
        "status": "catalog-only"
    }


class ImportValidationTests(unittest.TestCase):
    def test_accepts_explicit_source_backed_form(self):
        self.assertEqual(IMPORTERS.validate_form(valid_row()), [])

    def test_rejects_missing_effects_instead_of_guessing(self):
        row = valid_row()
        del row["effects"]["flags_written"]
        self.assertTrue(any("effects.flags_written is missing" in e
                            for e in IMPORTERS.validate_form(row)))

    def test_rejects_encoding_bits_outside_mask(self):
        row = valid_row()
        row["encoding"]["value"] = 0xffffffff
        self.assertTrue(any("outside encoding.mask" in e
                            for e in IMPORTERS.validate_form(row)))

    def test_rejects_unknown_architecture_alias(self):
        row = valid_row()
        row["architecture"] = "arm64-ish"
        self.assertTrue(any("unsupported or unnormalized" in e
                            for e in IMPORTERS.validate_form(row)))

    def test_conformance_claim_requires_evidence(self):
        row = valid_row()
        row["status"] = "conformance-tested"
        errors = IMPORTERS.validate_form(row)
        self.assertTrue(any("implementation_ref" in e for e in errors))
        self.assertTrue(any("conformance_test_ref" in e for e in errors))

    def test_encoding_endianness_must_be_explicit(self):
        row = valid_row()
        del row["encoding"]["byte_order"]
        self.assertTrue(any("byte_order must be explicit" in e
                            for e in IMPORTERS.validate_form(row)))


if __name__ == "__main__":
    unittest.main()
