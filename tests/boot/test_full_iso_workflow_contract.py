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

    def test_release_fails_without_real_userspace_handoff(self):
        workflow = Path(".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn("Fail build when any production target lacks a real CPL3 userspace handoff", workflow)
        self.assertIn("steps.userspace_gate.outputs.accepted", workflow)


if __name__ == "__main__":
    unittest.main()
