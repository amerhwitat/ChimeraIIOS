#!/usr/bin/env python3
"""Self-contained regression tests for tools/machine-code/identify.py."""
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("identify.py")
SPEC = importlib.util.spec_from_file_location("chimera_identify", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class IdentifyTests(unittest.TestCase):
    def test_elf_x86_64(self):
        data = bytearray(64)
        data[:6] = b"\x7fELF\x02\x01"
        data[18:20] = (62).to_bytes(2, "little")
        result = MODULE.identify(bytes(data))
        self.assertEqual((result["format"], result["architecture"], result["bits"]),
                         ("ELF", "x86_64", 64))

    def test_elf_big_endian_powerpc(self):
        data = bytearray(24)
        data[:6] = b"\x7fELF\x01\x02"
        data[18:20] = (20).to_bytes(2, "big")
        result = MODULE.identify(bytes(data))
        self.assertEqual(result["architecture"], "powerpc")
        self.assertEqual(result["endianness"], "big")

    def test_pe_x64(self):
        data = bytearray(128)
        data[:2] = b"MZ"
        data[0x3C:0x40] = (64).to_bytes(4, "little")
        data[64:68] = b"PE\0\0"
        data[68:70] = (0x8664).to_bytes(2, "little")
        self.assertEqual(MODULE.identify(bytes(data))["architecture"], "x86_64")

    def test_dos_mz_not_misidentified_as_pe(self):
        data = bytearray(64)
        data[:2] = b"MZ"
        self.assertEqual(MODULE.identify(bytes(data))["format"], "DOS MZ")

    def test_wasm(self):
        self.assertEqual(MODULE.identify(b"\0asm\x01\0\0\0")["format"], "WebAssembly")

    def test_unknown_bytes_are_not_guessed(self):
        result = MODULE.identify(b"\x90\x90\xcc\x00")
        self.assertEqual(result["architecture"], "unknown")
        self.assertEqual(result["execution_support"], "not_assessed")

    def test_truncated_elf(self):
        result = MODULE.identify(b"\x7fELF")
        self.assertEqual(result["identification_confidence"], "truncated")


if __name__ == "__main__":
    unittest.main()
