import importlib.util
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("binary_headers", ROOT / "tools/inspect-binary-headers.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class BinaryHeaderTests(unittest.TestCase):
    def test_elf64_x86_64(self):
        data = bytearray(64)
        data[:7] = b"\x7fELF\x02\x01\x01"
        data[18:20] = struct.pack("<H", 62)
        result = MODULE.inspect(bytes(data))
        self.assertEqual((result["format"], result["os"], result["architecture"], result["bits"]),
                         ("ELF", "Unix/Linux", "x86_64", 64))

    def test_pe_amd64(self):
        data = bytearray(128)
        data[:2] = b"MZ"
        data[0x3C:0x40] = struct.pack("<I", 64)
        data[64:68] = b"PE\0\0"
        data[68:70] = struct.pack("<H", 0x8664)
        result = MODULE.inspect(bytes(data))
        self.assertEqual((result["format"], result["os"], result["architecture"]),
                         ("PE/COFF", "Windows", "x86_64"))

    def test_macho_arm64(self):
        data = b"\xcf\xfa\xed\xfe" + struct.pack("<I", 0x0100000C) + bytes(32)
        result = MODULE.inspect(data)
        self.assertEqual((result["format"], result["os"], result["architecture"]),
                         ("Mach-O", "macOS/Darwin", "AArch64"))


    def test_java_class_and_universal_macho(self):
        java = b"\\xca\\xfe\\xba\\xbe" + struct.pack(">HH", 0, 65) + bytes(24)
        self.assertEqual(MODULE.inspect(java)["format"], "Java Class")
        fat = b"\\xca\\xfe\\xba\\xbe" + struct.pack(">I", 2) + bytes(24)
        self.assertEqual(MODULE.inspect(fat)["format"], "Mach-O Universal")

    def test_dos_and_wasm(self):
        mz = bytearray(64); mz[:2] = b"MZ"
        self.assertEqual(MODULE.inspect(bytes(mz))["format"], "DOS MZ")
        self.assertEqual(MODULE.inspect(b"\0asm\x01\0\0\0")["format"], "WebAssembly")

if __name__ == "__main__":
    unittest.main()
