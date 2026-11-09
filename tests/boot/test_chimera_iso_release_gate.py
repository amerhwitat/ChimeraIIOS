"""Regression tests that prevent publishing an ISO without real userspace evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/chimera-full-iso.yml"
PRODUCTION_TEST = ROOT / "tests/boot/test_production_target_handoff_qemu.py"
TRACE_VERIFIER = ROOT / "tests/boot/verify-userspace-handoff.py"


class ChimeraIsoReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.production_test = PRODUCTION_TEST.read_text(encoding="utf-8")
        cls.verifier = TRACE_VERIFIER.read_text(encoding="utf-8")

    def test_all_three_production_targets_use_real_trace_verifier(self):
        self.assertIn("id: userspace_gate", self.text)
        self.assertIn("python3 tests/boot/test_production_target_handoff_qemu.py", self.text)
        self.assertIn("--iso build/iso/chimera-ii-os.iso", self.text)
        self.assertIn("--output /tmp/chimera-userspace-traces", self.text)
        for target in ("live", "installer", "recovery"):
            self.assertIn(f'"{target}":', self.production_test)
        self.assertIn("target=(live|installer|recovery)", self.verifier)
        self.assertIn("verify-userspace-handoff.py", self.production_test)
        self.assertIn("USER INIT SYSCALL", self.verifier)
        self.assertIn("USERSPACE READY", self.verifier)

    def test_release_requires_runtime_gate_and_explicit_approval(self):
        release = self.text.split("      - name: Publish validated ISO candidate to GitHub Releases", 1)[1]
        condition = next(line for line in release.splitlines() if line.strip().startswith("if:"))
        self.assertIn("steps.userspace_gate.outputs.accepted == 'true'", condition)
        self.assertIn("vars.CHIMERA_RELEASE_ACCEPTANCE_APPROVED == 'true'", condition)

    def test_failed_handoff_uploads_traces_and_blocks_release(self):
        self.assertIn('echo "accepted=true" >> "$GITHUB_OUTPUT"', self.text)
        self.assertIn("Fail build when any production target lacks a real CPL3 userspace handoff", self.text)
        self.assertIn("if: steps.userspace_gate.outputs.accepted != 'true'", self.text)
        self.assertIn("name: Upload target-specific userspace acceptance traces", self.text)


if __name__ == "__main__":
    unittest.main()
