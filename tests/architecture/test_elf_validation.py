import importlib.util
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_elf_image", ROOT / "tools" / "validate_elf_image.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def fixture(machine=183, elf_class=2, entry=0x400000, filesz=4, memsz=4, p_align=1):
    # Synthetic parser fixture only; never a boot image.
    ident = b"\x7fELF" + bytes([elf_class, 1, 1, 0]) + bytes(8)
    if elf_class != 2:
        raise AssertionError("ELF64 fixture expected")
    ehdr = struct.pack("<HHIQQQIHHHHHH", 2, machine, 1, entry, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    phdr = struct.pack("<IIQQQQQQ", 1, 5, 0x100, 0x400000, 0x400000, filesz, memsz, p_align)
    data = bytearray(0x104)
    data[:16] = ident
    data[16:64] = ehdr
    data[64:120] = phdr
    data[0x100:0x104] = b"TEST"
    return bytes(data)

class ELFImageValidationTests(unittest.TestCase):
    def test_accepts_structurally_valid_aarch64_fixture(self):
        result = MODULE.validate_elf(fixture(), "aarch64")
        self.assertEqual(result["machine"], 183)
        self.assertEqual(result["load_segments"], 1)

    def test_rejects_machine_mismatch(self):
        with self.assertRaisesRegex(MODULE.ELFValidationError, "e_machine"):
            MODULE.validate_elf(fixture(machine=62), "aarch64")

    def test_rejects_entry_outside_load_segment(self):
        with self.assertRaisesRegex(MODULE.ELFValidationError, "entry point"):
            MODULE.validate_elf(fixture(entry=0x500000), "aarch64")

    def test_rejects_filesz_greater_than_memsz(self):
        with self.assertRaisesRegex(MODULE.ELFValidationError, "filesz exceeds"):
            MODULE.validate_elf(fixture(filesz=8, memsz=4), "aarch64")

    def test_rejects_truncated_input(self):
        with self.assertRaises(MODULE.ELFValidationError):
            MODULE.validate_elf(b"\x7fELF", "aarch64")

if __name__ == "__main__":
    unittest.main()
