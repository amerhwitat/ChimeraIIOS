import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class BootMenuTimeoutTests(unittest.TestCase):
    def assert_menu_policy(self, relative, seconds):
        text = Path(relative).read_text()
        self.assertRegex(text, rf"(?m)^set timeout={seconds}\s*$")
        self.assertRegex(text, r"(?m)^set timeout_style=menu\s*$")
        self.assertRegex(text, r"(?m)^set default=0\s*$")

    def test_primary_boot_menus_wait_five_minutes(self):
        for path in (
            "boot/iso/grub.cfg",
            "boot/jasper/jasper.cfg",
            "boot/loader-menu.cfg",
        ):
            with self.subTest(path=path):
                self.assert_menu_policy(path, 300)

    def test_jasper_spitfire_and_install_submenus_wait_two_minutes(self):
        for path in (
            "boot/jasper/live.cfg",
            "boot/jasper/install.cfg",
            "boot/jasper/recovery.cfg",
            "boot/jasper/diagnostics.cfg",
            "boot/jasper/retro.cfg",
            "boot/spitfire/spitfire-menu.cfg",
            "boot/installation/menu.cfg",
            "boot/installation/services.cfg",
            "boot/jasper/safe-mode.cfg",
            "boot/jasper/last-known-good.cfg",
        ):
            with self.subTest(path=path):
                self.assert_menu_policy(path, 120)

    def test_generated_jasper_recovery_menu_uses_two_minute_policy(self):
        script = Path("boot/iso/prepare-layout.sh").read_text()
        match = re.search(
            r'cat > "\$DIST/boot/jasper/recovery\.cfg" <<\'EOF\'\n(.*?)\nEOF',
            script,
            re.S,
        )
        self.assertIsNotNone(match, "Jasper recovery menu heredoc is missing")
        generated = match.group(1)
        self.assertIn("set timeout=120", generated)
        self.assertIn("set timeout_style=menu", generated)
        self.assertIn("set default=0", generated)

    def test_linux_live_images_generate_five_minute_grub_menu(self):
        script = Path("live-image/build.sh").read_text()
        self.assertIn('cat > "$ISODIR/boot/grub/grub.cfg" <<EOF', script)
        self.assertRegex(script, r"(?m)^set timeout=300$")
        self.assertRegex(script, r"(?m)^set timeout_style=menu$")
        self.assertRegex(script, r"(?m)^set default=0$")

    def test_gates_boot_contract_uses_long_timeout(self):
        gates = json.loads(Path("desktop/aurora/gates_menu.json").read_text())
        policy = gates["boot_menu_policy"]
        self.assertEqual(policy["timeout_seconds"], 300)
        self.assertEqual(policy["submenu_timeout_seconds"], 120)
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

    def test_octavian_shell_payload_is_merged_not_nested(self):
        script = Path("live-image/build.sh").read_text()
        self.assertIn('cp -a "$REPO_DIR/desktop/aurora-shell/." "$PAY/desktop/aurora-shell/"', script)
        self.assertNotIn('cp -a "$REPO_DIR/desktop/aurora-shell" "$PAY/desktop/aurora-shell"', script)

    def test_legacy_iso_generators_keep_the_primary_menu_visible_for_five_minutes(self):
        for path in (
            "Dockerfile.vmware",
            "Dockerfile.iso-builder",
            "generate-all-iso-editions.sh",
            "complete-build-system.sh",
            "generate-iso-from-docker.sh",
        ):
            with self.subTest(path=path):
                text = Path(path).read_text()
                self.assertIn("set default=0", text)
                self.assertIn("set timeout=300", text)
                self.assertIn("set timeout_style=menu", text)


if __name__ == "__main__":
    unittest.main()
