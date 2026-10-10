#!/usr/bin/env python3
"""Portable contract tests for endianness policy and freestanding helpers."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "system/architecture/endianness.json"
HEADER = ROOT / "kernel/include/chimera/endianness.h"


class EndiannessContractTests(unittest.TestCase):
    def test_contract_covers_modes_and_cpu_families(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("real_mode", data["modes"])
        self.assertIn("compatibility", data["modes"])
        self.assertIn("emulated", data["modes"])
        self.assertIn("mobile", data["modes"])
        for family in ("x86-16/real-mode", "x86-32/protected-mode",
                       "x86-64/long-mode", "arm32", "aarch64",
                       "riscv32", "riscv64", "mips32/64",
                       "powerpc32/64", "s390x"):
            self.assertIn(family, data["cpu_families"])
        self.assertEqual(data["canonical_wire"]["byte_order"], "little-endian")

    def test_freestanding_helpers_do_not_assume_native_endian(self):
        text = HEADER.read_text(encoding="utf-8")
        for symbol in ("chimera_load_le16", "chimera_load_le32",
                       "chimera_load_le64", "chimera_store_le16",
                       "chimera_store_le32", "chimera_store_le64",
                       "chimera_load_be16", "chimera_load_be32",
                       "chimera_load_be64", "chimera_store_be16",
                       "chimera_store_be32", "chimera_store_be64",
                       "chimera_native_endian"):
            self.assertIn(symbol, text)


if __name__ == "__main__":
    unittest.main()
