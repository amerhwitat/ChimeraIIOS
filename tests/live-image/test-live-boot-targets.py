#!/usr/bin/env python3
"""Static acceptance for the unified GRUB 2/Jasper/Spit Fire boot menu."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
MENU = (ROOT / "boot/jasper/live-image.cfg").read_text()
BUILDER = (ROOT / "live-image/build.sh").read_text()
GATES_CANDIDATES = [
    ROOT / "desktop/aurora/gates_menu.json",
    ROOT / "vendor/chimera-ii-os/source/desktop/aurora/gates_menu.json",
]
GATES_PATH = next((p for p in GATES_CANDIDATES if p.is_file()), None)


class UnifiedBootTargetTests(unittest.TestCase):
    def test_all_four_requested_targets_are_visible(self):
        for target_id in ("live-linux", "installer", "koronos", "recovery"):
            with self.subTest(target=target_id):
                self.assertIn(f"--id {target_id}", MENU)

    def test_highest_first_svga_and_framebuffer_handoff(self):
        self.assertIn("5120x2880,3840x2160", MENU)
        self.assertIn("set gfxpayload=keep", MENU)
        self.assertIn("1024x768,800x600,640x480", MENU)

    def test_verbose_boot_is_default_not_hidden_by_quiet(self):
        self.assertIn("loglevel=7 ignore_loglevel printk.time=1", MENU)
        self.assertIn("systemd.log_level=debug", MENU)
        self.assertIn("systemd.show_status=1", MENU)
        self.assertNotIn(" quiet ", MENU)

    def test_installer_fails_closed_without_native_payload(self):
        start = MENU.index("--id installer")
        end = MENU.index("\n}", start)
        entry = MENU[start:end]
        for required in ("koronos.elf", "installer-initrd.img", "installation.img",
                         "installer-contract.json", "installation_phases.json",
                         "installer_profiles.json"):
            self.assertIn(required, entry)
        self.assertIn("[INST BLOCKED]", entry)

    def test_koronos_is_not_claimed_as_production_userspace(self):
        start = MENU.index("--id koronos")
        end = MENU.index("\n}", start)
        entry = MENU[start:end]
        self.assertIn("experimental", MENU[start - 100:start + 30].lower())
        self.assertIn("koronos.elf", entry)
        self.assertIn("[KORO BLOCKED]", entry)

    def test_recovery_linux_rescue_shell_is_real_and_distinct(self):
        start = MENU.index("--id recovery {")
        end = MENU.index("\n}", start)
        entry = MENU[start:end]
        self.assertIn("chimera.mode=recovery", entry)
        self.assertIn("systemd.unit=multi-user.target", entry)
        self.assertNotIn("multiboot2", entry)
        self.assertIn("Recovery — Native Koronos Recovery", MENU)

    def test_builder_stages_menu_and_optional_native_payloads(self):
        for marker in ("boot/jasper/live-image.cfg", "KORONOS_ELF",
                       "INSTALLER_INITRAMFS", "INSTALLATION_IMAGE",
                       "RECOVERY_INITRAMFS", "boot/boot-targets.json",
                       "boot/jasper/jasper.cfg", "boot/spitfire/spitfire-menu.cfg"):
            self.assertIn(marker, BUILDER)

    def test_gates_exposes_matching_grub_actions(self):
        self.assertIsNotNone(GATES_PATH, "Gates menu JSON is required")
        gates = json.loads(GATES_PATH.read_text())
        for action in ("live", "install", "koronos", "recovery"):
            self.assertIn(action, gates["actions"])
        self.assertEqual(gates["actions"]["live"]["command"], "grub-reboot live-linux")
        self.assertEqual(gates["actions"]["koronos"]["command"], "grub-reboot koronos")
        self.assertEqual(gates["boot_targets"]["default"], "live-linux")
        self.assertTrue(gates["boot_targets"]["fail_closed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
