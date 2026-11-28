#!/usr/bin/env python3
"""Regression tests for isolating destructive native self-tests from production target boots."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = (ROOT / "kernel/core/native_stack.cpp").read_text()
BOOT = (ROOT / "kernel/core/koronos.cpp").read_text()


class NativeSelftestIsolationTests(unittest.TestCase):
    def test_production_user_init_skips_rebooting_persistence_selftest(self):
        self.assertIn("module->kind == CHIMERA_MODULE_USER_INIT_ELF", NATIVE)
        self.assertIn("production USER_INIT_ELF selected; destructive reboot self-test is test-boot only", NATIVE)
        self.assertIn("selftest_result_ = 1;", NATIVE)

    def test_skipped_production_gate_is_not_reported_as_pass(self):
        self.assertIn('native_rc == 1', BOOT)
        self.assertIn('self-test SKIPPED for production USER_INIT_ELF', BOOT)
        self.assertIn('native_rc == 1 && preempt_rc == 0 && smp_rc == 0', BOOT)

    def test_installer_media_skip_is_distinct_and_still_runs_installer_test(self):
        self.assertIn('selftest_result_ = 2;', NATIVE)
        self.assertIn('native_rc == 2', BOOT)
        self.assertIn('(native_rc == 0 || native_rc == 2)', BOOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
