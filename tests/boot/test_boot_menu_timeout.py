from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MENU_CONFIGS = (
    "boot/iso/grub.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/spitfire/spitfire-menu.cfg",
    "boot/installation/menu.cfg",
)

class BootMenuTimeoutTests(unittest.TestCase):
    def test_all_published_menu_layers_wait_thirty_seconds(self):
        for relative in MENU_CONFIGS:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertRegex(text, r"(?m)^set timeout=30$")
                self.assertRegex(text, r"(?m)^set timeout_style=menu$")

    def test_generated_recovery_menu_keeps_the_same_timeout(self):
        script = (ROOT / "boot/iso/prepare-layout.sh").read_text(encoding="utf-8")
        match = re.search(r"cat > \"\$DIST/boot/jasper/recovery\.cfg\" <<'EOF'\n(.*?)\nEOF", script, re.S)
        self.assertIsNotNone(match, "prepare-layout must generate the Jasper recovery menu")
        generated = match.group(1)
        self.assertIn("set timeout=30", generated)
        self.assertIn("set timeout_style=menu", generated)

if __name__ == "__main__":
    unittest.main()
