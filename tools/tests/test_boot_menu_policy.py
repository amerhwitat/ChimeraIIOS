"""Static regression tests for visible boot menus and explicit Gates selection."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MENU_PATHS = (
    "boot/iso/grub.cfg",
    "boot/installation/menu.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/jasper/safe-mode.cfg",
    "boot/jasper/last-known-good.cfg",
    "boot/spitfire/spitfire-menu.cfg",
)


class BootMenuPolicyTests(unittest.TestCase):
    def test_all_grub_menus_keep_the_120_second_visible_menu(self):
        for relative in MENU_PATHS:
            with self.subTest(menu=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                timeouts = re.findall(
                    r"^\s*set\s+timeout\s*=\s*([^\s#]+)", text, re.MULTILINE
                )
                styles = re.findall(
                    r"^\s*set\s+timeout_style\s*=\s*([^\s#]+)",
                    text,
                    re.MULTILINE,
                )
                self.assertEqual(
                    timeouts, ["120"],
                    f"{relative} must define one effective 120-second timeout",
                )
                self.assertEqual(
                    styles, ["menu"],
                    f"{relative} must keep the menu visible during its timeout",
                )

    def test_gates_requires_explicit_selection_and_returns_to_open_menu(self):
        config = json.loads(
            (ROOT / "desktop/aurora/gates_menu.json").read_text(encoding="utf-8")
        )
        policy = config["interaction"]["selection_policy"]
        self.assertIs(policy["wait_for_user_input"], True)
        self.assertIs(policy["auto_activate"], False)
        self.assertEqual(policy["timeout_seconds"], 300)
        self.assertEqual(policy["timeout_action"], "remain_open")
        self.assertIs(policy["selection_requires_explicit_confirmation"], True)


if __name__ == "__main__":
    unittest.main()
