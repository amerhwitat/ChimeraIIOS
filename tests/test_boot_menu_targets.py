from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT_CONFIGS = [
    ROOT / "boot/iso/grub.cfg",
    ROOT / "boot/jasper/jasper.cfg",
    ROOT / "boot/jasper/live.cfg",
    ROOT / "boot/jasper/install.cfg",
    ROOT / "boot/jasper/recovery.cfg",
    ROOT / "boot/jasper/diagnostics.cfg",
    ROOT / "boot/jasper/retro.cfg",
    ROOT / "boot/installation/menu.cfg",
    ROOT / "boot/spitfire/spitfire-menu.cfg",
]


class BootMenuTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in BOOT_CONFIGS}

    def test_all_configfile_targets_exist_in_repository(self):
        for source, content in self.sources.items():
            for target in re.findall(r"\bconfigfile\s+(/boot/[^\s}]+)", content):
                rel = target.lstrip("/")
                # The canonical ISO GRUB file is staged at /boot/grub/grub.cfg.
                if target == "/boot/grub/grub.cfg":
                    rel = "boot/iso/grub.cfg"
                with self.subTest(source=source, target=target):
                    self.assertTrue((ROOT / rel).is_file(), f"{source} references missing {target}")

    def test_all_kernel_boots_reference_staged_koronos(self):
        for source, content in self.sources.items():
            if "multiboot2 " in content:
                with self.subTest(source=source):
                    self.assertIn("multiboot2 /boot/koronos/koronos.elf", content)

    def test_boot_configs_only_reference_known_boot_payload_roots(self):
        allowed = ("/boot/live/", "/boot/recovery/", "/boot/visual/", "/install/installer/", "/system/hardware/")
        for source, content in self.sources.items():
            for path in re.findall(r"\b(?:module2|multiboot2)\s+(/[^\s]+)", content):
                with self.subTest(source=source, path=path):
                    self.assertTrue(path.startswith(allowed) or path == "/boot/koronos/koronos.elf", f"unexpected payload path {path}")

    def test_installer_menu_does_not_fall_back_to_live_as_installer(self):
        content = self.sources["boot/iso/grub.cfg"]
        match = re.search(r'menuentry "Chimera II OS — Install / Installer Environment[^\n]*--id install \{([\s\S]*?)\n\}', content)
        self.assertIsNotNone(match)
        body = match.group(1)
        self.assertIn("configfile /boot/jasper/install.cfg", body)
        self.assertIn("installation.img", body)
        self.assertNotIn("module2 /boot/live/chimera-live-initramfs.img", body)

    def test_retro_and_spitfire_menu_items_open_their_own_menus(self):
        content = self.sources["boot/iso/grub.cfg"]
        self.assertRegex(content, r'menuentry "Chimera II OS — Retro Computer Center" --id retro \{\s*configfile /boot/jasper/retro.cfg\s*\}')
        self.assertRegex(content, r'menuentry "Chimera II OS — Spit Fire Native Menu" --id spitfire \{\s*configfile /boot/spitfire/spitfire-menu.cfg\s*\}')

    def test_diagnostics_uses_real_recovery_payload_not_missing_manifest(self):
        for source in ("boot/iso/grub.cfg", "boot/jasper/diagnostics.cfg"):
            content = self.sources[source]
            self.assertIn("/boot/recovery/chimera-recovery-initramfs.img", content)
            self.assertIn("/boot/recovery/recovery-manifest.json", content)
            self.assertNotIn("/boot/diagnostics/diagnostics-manifest.json", content)

    def test_x86_64_iso_does_not_claim_arm64_kernel_boot(self):
        for source in ("boot/iso/grub.cfg", "boot/jasper/jasper.cfg"):
            content = self.sources[source]
            self.assertRegex(content, r"Mobile / ARM64[^\n]*\n(?:[^\n]*\n){0,4}[^\n]*(?:x86_64 Koronos kernel only|matching kernel and device-specific boot chain|matching kernel and device-specific boot chain)")


if __name__ == "__main__":
    unittest.main()
