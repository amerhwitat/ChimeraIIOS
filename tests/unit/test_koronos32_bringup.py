#!/usr/bin/env python3
"""Static contract tests for the independent x86-32 Koronos bring-up probe."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCH = ROOT / "kernel" / "arch" / "x86_32"


class Koronos32BringupContractTests(unittest.TestCase):
    def test_multiboot_entry_and_elf32_link_contract_exist(self):
        boot = (ARCH / "boot.S").read_text(encoding="utf-8")
        linker = (ARCH / "linker.ld").read_text(encoding="utf-8")
        makefile = (ARCH / "Makefile").read_text(encoding="utf-8")
        self.assertIn("0x1BADB002", boot)
        self.assertIn("ENTRY(_start)", linker)
        self.assertIn("elf32-i386", linker)
        self.assertIn("-m32", makefile)
        self.assertIn("ELF32", makefile)

    def test_probe_does_not_claim_full_kernel(self):
        source = (ARCH / "kernel.c").read_text(encoding="utf-8")
        script = (ROOT / "tools" / "runtime" / "check-koronos32-boot.sh").read_text(encoding="utf-8")
        self.assertIn("KORONOS32_BOOT_OK", source)
        self.assertIn("serial-probe-only", source)
        self.assertIn("not the production Koronos kernel", script)


if __name__ == "__main__":
    unittest.main()
