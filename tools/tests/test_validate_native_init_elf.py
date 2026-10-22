#!/usr/bin/env python3
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate-native-init-elf.py"
SPEC = importlib.util.spec_from_file_location("validate_native_init_elf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_elf(*, machine=62, e_type=2, flags=5, entry=0x100000001):
    ident = b"\x7fELF" + bytes([2, 1, 1]) + bytes(9)
    ehdr = MODULE.ELF_HEADER.pack(
        ident, e_type, machine, 1, entry, MODULE.ELF_HEADER.size, 0, 0,
        MODULE.ELF_HEADER.size, MODULE.PROGRAM_HEADER.size, 1, 0, 0, 0
    )
    phdr = MODULE.PROGRAM_HEADER.pack(1, flags, 0x100, 0x100000000, 0, 4, 4, 0x1000)
    return ehdr + phdr + bytes(0x100 - len(ehdr) - len(phdr)) + b"CODE"


class NativeInitElfContractTests(unittest.TestCase):
    def test_accepts_minimal_x86_64_exec_with_rx_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init.elf"
            path.write_bytes(make_elf())
            MODULE.validate(path, "live")

    def test_rejects_shell_script(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init"
            path.write_text("#!/bin/sh\nexec /bin/sh\n")
            with self.assertRaisesRegex(ValueError, "not an ELF"):
                MODULE.validate(path, "live")

    def test_rejects_wrong_machine(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init.elf"
            path.write_bytes(make_elf(machine=183))
            with self.assertRaisesRegex(ValueError, "EM_X86_64"):
                MODULE.validate(path, "live")

    def test_rejects_writable_executable_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init.elf"
            path.write_bytes(make_elf(flags=7))
            with self.assertRaisesRegex(ValueError, r"W\^X"):
                MODULE.validate(path, "live")

    def test_rejects_entry_outside_executable_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init.elf"
            path.write_bytes(make_elf(entry=0x100000200))
            with self.assertRaisesRegex(ValueError, "entry point"):
                MODULE.validate(path, "live")

    def test_rejects_invalid_target(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "init.elf"
            path.write_bytes(make_elf())
            with self.assertRaisesRegex(ValueError, "unsupported target"):
                MODULE.validate(path, "mobile")


if __name__ == "__main__":
    unittest.main()
