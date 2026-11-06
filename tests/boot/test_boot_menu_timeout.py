#!/usr/bin/env python3
"""Regression tests for interactive boot-menu timeout and Gates selection policy."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENU_FILES = (
    "boot/iso/grub.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/jasper/last-known-good.cfg",
    "boot/jasper/safe-mode.cfg",
    "boot/spitfire/spitfire-menu.cfg",
    "boot/installation/menu.cfg",
    "boot/installation/services.cfg",
    "boot/loader-menu.cfg",
)


class InteractiveBootMenuTests(unittest.TestCase):
    def test_all_grub_menu_configs_wait_sixty_seconds(self):
        for relative in MENU_FILES:
            with self.subTest(menu=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertRegex(content, r"(?m)^set timeout=60\\s*$")
                self.assertRegex(content, r"(?m)^set timeout_style=menu\\s*$")
                self.assertRegex(content, r"(?m)^set default=0\\s*$")

    def test_generated_jasper_recovery_menu_keeps_timeout(self):
        script = (ROOT / "boot/iso/prepare-layout.sh").read_text(encoding="utf-8")
        match = re.search(
            r'cat > "\\$DIST/boot/jasper/recovery\\.cfg" <<\'EOF\'\\n(.*?)\\nEOF',
            script,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "generated Jasper recovery config heredoc is missing")
        generated = match.group(1)
        self.assertRegex(generated, r"(?m)^set timeout=60\\s*$")
        self.assertRegex(generated, r"(?m)^set timeout_style=menu\\s*$")
        self.assertRegex(generated, r"(?m)^set default=0\\s*$")

    def test_gates_requires_explicit_selection_and_never_autoselects(self):
        gates = json.loads((ROOT / "desktop/aurora/gates_menu.json").read_text(encoding="utf-8"))
        policy = gates["input_policy"]
        self.assertIs(policy["requires_explicit_user_selection"], True)
        self.assertIs(policy["auto_select_default"], False)
        self.assertEqual(policy["idle_timeout_action"], "remain_on_menu")

    def test_boot_contract_documents_menu_policy(self):
        contract = json.loads((ROOT / "boot/boot-menu-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["menu_timeout_seconds"], 60)
        self.assertEqual(contract["timeout_style"], "menu")
        self.assertFalse(contract["gates_input_policy"]["auto_select_default"])


if __name__ == "__main__":
    unittest.main()
