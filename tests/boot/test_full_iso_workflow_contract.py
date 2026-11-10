from pathlib import Path
import unittest


class FullIsoWorkflowContractTests(unittest.TestCase):
    def test_canonical_native_builder_is_selected(self):
        workflow = Path(".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn('CHIMERA_BUILD_NATIVE_ISO_PIPELINE: "1"', workflow)
        self.assertIn("./build-chimera-iso.sh --clean-state", workflow)

    def test_native_iso_dependencies_are_installed(self):
        workflow = Path(".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn("squashfs-tools jq rsync", workflow)

    def test_build_scripts_are_syntax_checked_and_final_efi_is_required(self):
        workflow = Path(".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        builder = Path("build-chimera-iso.sh").read_text(encoding="utf-8")
        self.assertIn("bash -n build-chimera-iso.sh", workflow)
        self.assertIn("bash -n kernel/build-koronos.sh", workflow)
        self.assertIn("extract /EFI/BOOT/BOOTX64.EFI", workflow)
        self.assertIn("Hybrid ISO is missing /EFI/BOOT/BOOTX64.EFI", builder)
        self.assertIn("Preserve the EFI executable from the finished ISO itself", builder)

    def test_release_fails_without_real_userspace_handoff(self):
        workflow = Path(".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn("Fail build when any production target lacks a real CPL3 userspace handoff", workflow)
        self.assertIn("steps.userspace_gate.outputs.accepted", workflow)


if __name__ == "__main__":
    unittest.main()
