#!/usr/bin/env python3
import importlib.util
import json
import struct
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("chimera_machine_code",HERE/"chimera-machine-code.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IdentificationTests(unittest.TestCase):
    def test_elf_x86_64_header(self):
        b=bytearray(64); b[:4]=b"\x7fELF"; b[4]=2; b[5]=1
        struct.pack_into("<H",b,18,62)
        r=mod.identify_bytes(bytes(b))
        self.assertEqual((r["format"],r["architecture"]),("ELF","x86_64"))
    def test_elf_riscv_class_separates_32_and_64(self):
        for cls,expected in ((1,"riscv32"),(2,"riscv64")):
            b=bytearray(64); b[:4]=b"\x7fELF"; b[4]=cls; b[5]=1
            struct.pack_into("<H",b,18,243)
            self.assertEqual(mod.identify_bytes(bytes(b))["architecture"],expected)
    def test_elf_machine_and_class_must_both_match(self):
        b=bytearray(64); b[:4]=b"\x7fELF"; b[4]=2; b[5]=1
        struct.pack_into("<H",b,18,3)
        self.assertEqual(mod.identify_bytes(bytes(b))["architecture"],"unknown")
    def test_pe_x86_64(self):
        b=bytearray(128); b[:2]=b"MZ"; struct.pack_into("<I",b,0x3c,64)
        b[64:68]=b"PE\0\0"; struct.pack_into("<H",b,68,0x8664)
        r=mod.identify_bytes(bytes(b))
        self.assertEqual((r["format"],r["architecture"]),("PE/COFF","x86_64"))
    def test_wasm_magic(self):
        self.assertEqual(mod.identify_bytes(b"\0asm\x01\0\0\0")["architecture"],"wasm32")
    def test_unknown_does_not_guess_arch(self):
        self.assertEqual(mod.identify_bytes(b"\x90\x90\x90")["architecture"],"unknown")
    def test_raw_requires_explicit_registered_arch(self):
        self.assertEqual(mod.identify_bytes(b"abc","rv64")["architecture"],"riscv64")
        with self.assertRaises(ValueError): mod.identify_bytes(b"abc","not-a-cpu")
    def test_registry_arches_have_status_boundary(self):
        db=json.loads((HERE/"architecture-backends.json").read_text())
        self.assertIn("riscv64",db["architectures"])
        self.assertIn("x86_64",db["architectures"])
        self.assertEqual(db["architectures"]["x86"]["elf_class"],1)
        self.assertEqual(db["architectures"]["x86_64"]["elf_class"],2)
        self.assertTrue(db["safety"]["never_execute_unknown_raw_bytes"])

if __name__=="__main__": unittest.main(verbosity=2)
