import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("verify_aarch64_linker_entry", ROOT / "tools" / "verify_aarch64_linker_entry.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

GOOD_SCRIPT = """
OUTPUT_FORMAT(elf64-littleaarch64)
OUTPUT_ARCH(aarch64)
ENTRY(kernel_entry)
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS { .text : { *(.text.entry) *(.text*) } :text }
"""
class TestAArch64EntryVerifier(unittest.TestCase):
    def test_accepts_required_script_and_defined_symbol(self):
        MOD.validate_entry_symbol(GOOD_SCRIPT, "0000000040000000 T kernel_entry\n")

    def test_rejects_missing_entry_directive(self):
        with self.assertRaisesRegex(MOD.ContractError, "ENTRY"):
            MOD.validate_linker_script(GOOD_SCRIPT.replace("ENTRY(kernel_entry)", "ENTRY(_start)"))

    def test_rejects_wrong_architecture(self):
        with self.assertRaisesRegex(MOD.ContractError, "OUTPUT_ARCH"):
            MOD.validate_linker_script(GOOD_SCRIPT.replace("OUTPUT_ARCH(aarch64)", "OUTPUT_ARCH(i386:x86-64)"))

    def test_rejects_missing_load_segment(self):
        with self.assertRaisesRegex(MOD.ContractError, "PT_LOAD"):
            MOD.validate_linker_script(GOOD_SCRIPT.replace("PT_LOAD", "PT_NULL"))

    def test_rejects_elf_without_entry_symbol(self):
        with self.assertRaisesRegex(MOD.ContractError, "does not define kernel_entry"):
            MOD.validate_entry_symbol(GOOD_SCRIPT, "0000000040000000 T _start\n")

if __name__ == "__main__":
    unittest.main()
