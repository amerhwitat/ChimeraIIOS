"""Regression tests that prevent publishing an ISO without real userspace evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/chimera-full-iso.yml"
FULL_ISO_BUILDER = ROOT / "tools/build-full-iso.sh"

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

    def test_unverified_handoff_fails_workflow_after_artifacts_are_uploaded(self):
        upload = self.text.index("name: Upload ISO artifacts")
        fail = self.text.index("name: Fail the workflow when production userspace acceptance is unverified")
        publish = self.text.index("name: Publish validated ISO candidate to GitHub Releases")
        self.assertLess(upload, fail)
        self.assertLess(fail, publish)
        self.assertIn("if: steps.userspace_gate.outputs.accepted != 'true'", self.text[fail:publish])
        self.assertIn("exit 1", self.text[fail:publish])

    def test_full_iso_uses_canonical_kernel_and_stages_real_target_init_elfs(self):
        builder = FULL_ISO_BUILDER.read_text(encoding="utf-8")
        self.assertIn('bash "$ROOT/kernel/build-koronos.sh"', builder)
        self.assertIn('CHIMERA_INIT_STAGE_DIR="$ROOT/build/live-boot" bash "$ROOT/tools/build-production-init-elfs.sh"', builder)
        self.assertIn('cmp "$KERNEL" "$INIT_VERIFY/koronos.elf"', builder)
        self.assertIn('tools/validate-native-init-elf.py', builder)
        for target in ("live", "installer", "recovery"):
            self.assertIn(f"user-init-{target}.elf", builder)
            self.assertIn(f"chimera-user-init-elf target={target}", builder)

if __name__ == "__main__":
    unittest.main()
