import importlib.util
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("binary_headers",ROOT/"tools/inspect-binary-headers.py")
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)

class BinaryHeaderTests(unittest.TestCase):
    def test_elf64_x86_64_and_entry(self):
        data=bytearray(64);data[:7]=b"\x7fELF\x02\x01\x01";data[16:18]=struct.pack("<H",2)
        data[18:20]=struct.pack("<H",62);data[24:32]=struct.pack("<Q",0x401000)
        result=MODULE.inspect(bytes(data))
        self.assertEqual((result["format"],result["os"],result["architecture"],result["bits"]),("ELF","Unix/Linux","x86_64",64))
        self.assertEqual(result["file_type"],"executable");self.assertEqual(result["entry_point"],"0x401000")

    def test_pe_amd64_optional_header_and_subsystem(self):
        data=bytearray(256);data[:2]=b"MZ";data[0x3C:0x40]=struct.pack("<I",64)
        data[64:68]=b"PE\0\0";data[68:70]=struct.pack("<H",0x8664)
        data[70:72]=struct.pack("<H",3);data[64+20:64+22]=struct.pack("<H",0xF0)
        opt=64+24;data[opt:opt+2]=struct.pack("<H",0x20B);data[opt+16:opt+20]=struct.pack("<I",0x1000)
        data[opt+68:opt+70]=struct.pack("<H",3)
        result=MODULE.inspect(bytes(data))
        self.assertEqual((result["format"],result["os"],result["architecture"]),("PE/COFF","Windows","x86_64"))
        self.assertEqual(result["optional_header"],"PE32+");self.assertEqual(result["subsystem"],"windows-console")

    def test_macho_arm64(self):
        data=b"\xcf\xfa\xed\xfe"+struct.pack("<IIII",0x0100000C,0,2,0)+bytes(20)
        result=MODULE.inspect(data)
        self.assertEqual((result["format"],result["os"],result["architecture"]),("Mach-O","macOS/Darwin","AArch64"))

    def test_java_and_universal_macho_arches(self):
        java=bytes.fromhex("cafebabe")+struct.pack(">HH",0,65)+bytes(24)
        self.assertEqual(MODULE.inspect(java)["format"],"Java Class")
        fat=bytes.fromhex("cafebabe")+struct.pack(">I",2)+struct.pack(">IIIII",7,3,0,100,2)+struct.pack(">IIIII",0x01000007,3,100,100,2)
        r=MODULE.inspect(fat);self.assertEqual(r["format"],"Mach-O Universal")
        self.assertEqual(r["architectures"],["i386","x86_64"])

    def test_dos_and_wasm(self):
        mz=bytearray(64);mz[:2]=b"MZ";self.assertEqual(MODULE.inspect(bytes(mz))["format"],"DOS MZ")
        self.assertEqual(MODULE.inspect(b"\0asm\x01\0\0\0")["format"],"WebAssembly")

if __name__=="__main__":unittest.main()
