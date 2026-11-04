"""Regression tests that prevent publishing an ISO without real userspace evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/chimera-full-iso.yml"


class ChimeraIsoReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_live_target_uses_real_trace_verifier_and_native_targets_stay_blocked(self):
        self.assertIn("id: userspace_gate", self.text)
        self.assertIn('verify-userspace-handoff.py live "$trace"', self.text)
        self.assertIn("native-installer-runtime.ready", self.text)
        self.assertIn("native-recovery-runtime.ready", self.text)
        self.assertIn("Native Installer: BLOCKED", self.text)
        self.assertIn("Native Koronos Recovery: BLOCKED", self.text)
        self.assertIn("prototype-built-not-native-koronos-runtime", self.text)

    def test_release_requires_runtime_gate_and_explicit_approval(self):
        release = self.text.split("      - name: Publish validated ISO candidate to GitHub Releases", 1)[1]
        condition = next(line for line in release.splitlines() if line.strip().startswith("if:"))
        self.assertIn("steps.userspace_gate.outputs.accepted == 'true'", condition)
        self.assertIn("vars.CHIMERA_RELEASE_ACCEPTANCE_APPROVED == 'true'", condition)

    def test_unverified_handoff_keeps_build_reviewable_but_blocks_release(self):
        self.assertIn('echo "accepted=$accepted" >> "$GITHUB_OUTPUT"', self.text)
        self.assertIn("no release will be published", self.text)
        self.assertIn("name: Upload target-specific userspace acceptance traces", self.text)


if __name__ == "__main__":
    unittest.main()
