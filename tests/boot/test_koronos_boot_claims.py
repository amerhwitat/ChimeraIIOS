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


if __name__ == "__main__":
    unittest.main()
