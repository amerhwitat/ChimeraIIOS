"""Regression tests that prevent publishing an ISO without real userspace evidence."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/chimera-full-iso.yml"
BOOT_MENU_FILES = (
    "boot/iso/grub.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/jasper/safe-mode.cfg",
    "boot/jasper/last-known-good.cfg",
    "boot/installation/menu.cfg",
    "boot/spitfire/spitfire-menu.cfg",
)

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
        self.assertIn("steps.six_case_gate.outputs.accepted == 'true'", condition)
        self.assertIn("vars.CHIMERA_RELEASE_ACCEPTANCE_APPROVED == 'true'", condition)

    def test_release_uses_original_iso_for_all_six_cases(self):
        self.assertIn("id: six_case_gate", self.text)
        self.assertIn("verify-six-case-matrix.py --iso \"$iso\"", self.text)
        self.assertIn("one identical ISO SHA across Live/Installer/Recovery", self.text)
        self.assertIn("diagnostic probes, not six-case release evidence", self.text)

    def test_legacy_tag_release_path_is_fail_closed(self):
        legacy = (ROOT / ".github/workflows/chimera-release.yml").read_text(encoding="utf-8")
        guard = legacy.index("Refuse legacy bootstrap ISO publication")
        publish = legacy.index("Publish GitHub Release")
        self.assertLess(guard, publish)
        self.assertIn("exit 1", legacy[guard:publish])
        self.assertIn("canonical full native Koronos ISO", legacy[guard:publish])

    def test_unverified_handoff_keeps_build_reviewable_but_blocks_release(self):
        self.assertIn('echo "accepted=$accepted" >> "$GITHUB_OUTPUT"', self.text)
        self.assertIn("no release will be published", self.text)
        self.assertIn("name: Upload target-specific userspace acceptance traces", self.text)

    def test_visible_boot_menus_and_native_init_modules(self):
        for relative in BOOT_MENU_FILES:
            menu = ROOT / relative
            text = menu.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^set timeout=120$")
            self.assertRegex(text, r"(?m)^set timeout_style=menu$")
            blocks = re.split(r"(?m)(?=^menuentry\b)", text)
            for block in blocks:
                if "multiboot2 " not in block:
                    continue
                modules = re.findall(
                    r"(?m)^\s*module2\s+/boot/targets/target-init-(live|installer|recovery)\.elf\s+"
                    r"chimera-user-init-elf\s+target=(live|installer|recovery)\s+firmware=\$grub_platform\s*$",
                    block,
                )
                self.assertEqual(
                    len(modules), 1,
                    f"{relative}: every Koronos boot entry must stage exactly one native init ELF",
                )
                self.assertEqual(
                    modules[0][0], modules[0][1],
                    f"{relative}: target-init ELF and target handoff must agree",
                )

    def test_gates_requires_explicit_selection_and_remains_open(self):
        gates = json.loads((ROOT / "desktop/aurora/gates_menu.json").read_text(encoding="utf-8"))
        selection = gates["interaction"]["selection_policy"]
        self.assertIs(selection.get("wait_for_user_input"), True)
        self.assertIs(selection.get("auto_activate"), False)
        self.assertEqual(selection.get("timeout_seconds"), 300)
        self.assertEqual(selection.get("timeout_action"), "remain_open")
        self.assertIs(selection.get("selection_requires_explicit_confirmation"), True)

if __name__ == "__main__":
    unittest.main()
