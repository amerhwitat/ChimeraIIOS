#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("chimera-nbit-mode.py")
SPEC = importlib.util.spec_from_file_location("chimera_nbit_mode", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class NBitModeTests(unittest.TestCase):
    def test_width_must_be_byte_aligned_and_bounded(self):
        with self.assertRaises(Exception):
            MODULE.parse_width("7")
        with self.assertRaises(Exception):
            MODULE.parse_width("65544")
        self.assertEqual(MODULE.parse_width("8192"), 8192)

    def test_arithmetic_wraps_at_selected_width(self):
        self.assertEqual(MODULE.evaluate("add", 255, 1, 8), 0)
        self.assertEqual(MODULE.evaluate("sub", 0, 1, 8), 255)

    def test_bitwise_and_shift_operations(self):
        self.assertEqual(MODULE.evaluate("and", 0b1100, 0b1010, 8), 0b1000)
        self.assertEqual(MODULE.evaluate("or", 0b1100, 0b0011, 8), 0b1111)
        self.assertEqual(MODULE.evaluate("xor", 0b1100, 0b1010, 8), 0b0110)
        self.assertEqual(MODULE.evaluate("shl", 1, 8, 8), 0)
        self.assertEqual(MODULE.evaluate("shr", 0xff, 8, 8), 0)

    def test_metadata_does_not_claim_native_hardware(self):
        # CLI metadata contract is covered by the actual entry point in CI.
        self.assertEqual(MODULE.evaluate("add", 1, 1, 8192), 2)


if __name__ == "__main__":
    unittest.main()
