import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class BootMenuTimeoutTests(unittest.TestCase):
    def test_published_menu_configs_wait_sixty_seconds(self):
        paths = [
            "boot/iso/grub.cfg",
            "boot/loader-menu.cfg",
            "boot/jasper/jasper.cfg",
            "boot/jasper/live.cfg",
            "boot/jasper/install.cfg",
            "boot/jasper/recovery.cfg",
            "boot/jasper/diagnostics.cfg",
            "boot/jasper/retro.cfg",
            "boot/spitfire/spitfire-menu.cfg",
            "boot/installation/menu.cfg",
        ]
        for relative in paths:
            with self.subTest(path=relative):
                text = Path(relative).read_text()
                self.assertRegex(text, r"(?m)^set timeout=60\s*$")
                self.assertRegex(text, r"(?m)^set timeout_style=menu\s*$")
                self.assertRegex(text, r"(?m)^set default=0\s*$")

    def test_generated_jasper_recovery_menu_uses_same_policy(self):
        script = Path("boot/iso/prepare-layout.sh").read_text()
        match = re.search(
            r'cat > "\$DIST/boot/jasper/recovery\.cfg" <<\'EOF\'\n(.*?)\nEOF',
            script,
            re.S,
        )
        self.assertIsNotNone(match, "Jasper recovery menu heredoc is missing")
        generated = match.group(1)
        self.assertIn("set timeout=60", generated)
        self.assertIn("set timeout_style=menu", generated)
        self.assertIn("set default=0", generated)


    def test_both_live_image_builds_generate_sixty_second_grub_menu(self):
        script = Path("live-image/build.sh").read_text()
        self.assertIn('cat > "$ISODIR/boot/grub/grub.cfg" <<EOF', script)
        self.assertRegex(script, r"(?m)^set timeout=60$")
        self.assertRegex(script, r"(?m)^set timeout_style=menu$")
        self.assertRegex(script, r"(?m)^set default=0$")

    def test_gates_defaults_only_after_sixty_second_wait(self):
        gates = json.loads(Path("desktop/aurora/gates_menu.json").read_text())
        policy = gates["boot_menu_policy"]
        self.assertEqual(policy["timeout_seconds"], 60)
        self.assertEqual(policy["timeout_style"], "menu")
        self.assertEqual(policy["on_timeout"], "boot_configured_default")
        self.assertEqual(policy["default_index"], 0)

    def test_userspace_tmpfiles_declaration_is_installed(self):
        source = Path("userspace/tmpfiles/aurora.conf")
        self.assertTrue(source.is_file())
        with tempfile.TemporaryDirectory() as destdir:
            subprocess.run(
                ["make", "-C", "userspace", "install", f"DESTDIR={destdir}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            installed = Path(destdir) / "usr/lib/tmpfiles.d/aurora.conf"
            self.assertTrue(installed.is_file())
            self.assertEqual(installed.read_text(), source.read_text())


if __name__ == "__main__":
    unittest.main()
