import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class GatesMenuContractTests(unittest.TestCase):
    def test_gates_menu_is_referenced_by_jasper_and_grub(self):
        jasper = (ROOT / "boot/jasper/jasper.cfg").read_text()
        grub = (ROOT / "boot/iso/grub.cfg").read_text()
        self.assertIn("configfile /boot/gates/gates.cfg", jasper)
        self.assertIn("configfile /boot/gates/gates.cfg", grub)

    def test_jasper_and_gates_are_single_top_level_grub_entries(self):
        grub = (ROOT / "boot/iso/grub.cfg").read_text()
        self.assertEqual(grub.count("--id jasper"), 1)
        self.assertEqual(grub.count("--id gates"), 1)
        jasper_at = grub.index('--id jasper')
        firmware_guards = [i for i in range(len(grub))
                           if grub.startswith('if [ "$grub_platform" = efi ]; then', i)]
        self.assertGreaterEqual(len(firmware_guards), 2)
        # The Jasper menu must precede the EFI-only submenu block so BIOS users
        # can also enter Jasper. The first guard only loads EFI GRUB modules.
        self.assertLess(jasper_at, firmware_guards[1])
        self.assertIn("configfile /boot/jasper/jasper.cfg", grub)

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
        self.assertIn("prepare-layout.sh", builder)
        layout = (ROOT / "boot/iso/prepare-layout.sh").read_text()
        self.assertIn("boot/gates/gates.cfg", layout)
        self.assertIn("boot/gates/gates.cfg", validator)

    def test_gates_menu_guards_uefi_chainloading(self):
        gates = (ROOT / "boot/gates/gates.cfg").read_text()
        self.assertIn('if [ "$grub_platform" = efi ]', gates)
        self.assertIn("fwsetup", gates)
        self.assertIn("Windows Boot Manager", gates)
        self.assertIn("Linux EFI Loader", gates)

if __name__ == "__main__":
    unittest.main()
