"""Prevent Koronos boot logs from claiming services or target execution that is not wired."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "kernel" / "core" / "koronos.cpp"


class KoronosBootClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_unimplemented_services_are_not_reported_as_running(self):
        for misleading in (
            "Core storage/security/logging services active",
            "Hardware discovery service started",
            "Storage discovery service started",
            "Initializing installer services in parallel",
            "Service orchestration online",
        ):
            with self.subTest(message=misleading):
                self.assertNotIn(misleading, self.source)

    def test_target_handoff_is_reported_as_blocked_until_native_runtime_exists(self):
        self.assertIn("no native ring-3 init entry path is connected", self.source)
        self.assertIn("no process-backed installer workers are connected", self.source)
        self.assertIn("Storage/security/logging backends remain DECLARED, not RUNNING", self.source)
        self.assertIn("No production installer init ELF is present; refusing readiness", self.source)

    def test_bootloader_keeps_svga_until_target_handoff(self):
        boot_configs = (
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
        for relative in boot_configs:
            with self.subTest(config=relative):
                config = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("set gfxmode=800x600,640x480", config)
                self.assertIn("set gfxpayload=keep", config)
                self.assertNotRegex(config, r"(?m)^set gfxmode=.*(?:1024x768|1280x|1366x|1440x|1600x|1920x|2560x|3840x|5120x|,auto)")


if __name__ == "__main__":
    unittest.main()
