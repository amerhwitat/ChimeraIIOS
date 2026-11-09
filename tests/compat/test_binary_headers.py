import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/binary/inspect_binary.py"
SPEC = importlib.util.spec_from_file_location("chm_binary_inspect", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class BinaryHeaderTests(unittest.TestCase):
    def test_elf64_x86_64(self):
        data = bytearray(64)
        data[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<HH", data, 16, 2, 62)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(data)
            result = MODULE.parse(path)
        self.assertEqual((result["format"], result["bits"], result["architecture"]), ("ELF", 64, "x86-64"))
        self.assertFalse(result["executed"])

    def test_pe32_plus_amd64(self):
        data = bytearray(256)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 0x80)
        data[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 1, 0, 0, 0, 0xF0, 0x22)
        struct.pack_into("<H", data, 0x98, 0x20B)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(data)
            result = MODULE.parse(path)
        self.assertEqual((result["format"], result["bits"], result["architecture"]), ("PE/COFF", 64, "x86-64"))

    def test_macho_arm64(self):
        data = bytearray(32)
        data[:4] = b"\xcf\xfa\xed\xfe"
        struct.pack_into("<IIIIII", data, 4, 0x0100000C, 0, 2, 1, 0, 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(data)
            result = MODULE.parse(path)
        self.assertEqual((result["format"], result["bits"], result["architecture"]), ("Mach-O", 64, "AArch64"))

    def test_truncated_elf_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "truncated.bin"
            path.write_bytes(b"\x7fELF\x02")
            with self.assertRaises(ValueError):
                MODULE.parse(path)

if __name__ == "__main__":
    unittest.main()
