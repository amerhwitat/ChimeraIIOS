"""Regression tests that prevent publishing an ISO without real userspace evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/chimera-full-iso.yml"

class ChimeraIsoReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_all_three_targets_use_real_trace_verifier(self):
        self.assertIn("id: userspace_gate", self.text)
        for target in ("live", "installer", "recovery"):
            self.assertIn(f'for target in live installer recovery', self.text)
            self.assertIn(f'python3 tests/boot/verify-userspace-handoff.py "$target" "$trace"', self.text)
        self.assertIn("verify-userspace-handoff.py", self.text)

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
