import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class GatesMenuContractTests(unittest.TestCase):
    def test_gates_menu_is_referenced_by_jasper_and_grub(self):
        jasper = (ROOT / "boot/jasper/jasper.cfg").read_text()
        grub = (ROOT / "boot/iso/grub.cfg").read_text()
        self.assertIn("configfile /boot/gates/gates.cfg", jasper)
        self.assertIn("configfile /boot/gates/gates.cfg", grub)

    def test_gates_menu_is_staged_and_verified(self):
        build = (ROOT / "build-chimera-iso.sh").read_text()
        self.assertIn('"$SCRIPT_DIR/boot/gates"', build)
        self.assertIn("/boot/gates/gates.cfg", build)

    def test_contract_declares_gates(self):
        contract = json.loads((ROOT / "boot/boot-menu-contract.json").read_text())
        self.assertIn("gates", contract["entries"])
        self.assertEqual(contract["gates_config"], "/boot/gates/gates.cfg")

    def test_canonical_iso_builder_stages_and_requires_gates(self):
        builder = (ROOT / "boot/iso/build-iso.sh").read_text()
        validator = (ROOT / "boot/iso/validate-iso.py").read_text()
        self.assertIn("boot/gates/gates.cfg", builder)
        self.assertIn("boot/gates/gates.cfg", validator)

    def test_gates_menu_guards_uefi_chainloading(self):
        gates = (ROOT / "boot/gates/gates.cfg").read_text()
        self.assertIn('if [ "$grub_platform" = efi ]', gates)
        self.assertIn("fwsetup", gates)
        self.assertIn("Windows Boot Manager", gates)
        self.assertIn("Linux EFI Loader", gates)

if __name__ == "__main__":
    unittest.main()
