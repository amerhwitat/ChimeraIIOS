#!/usr/bin/env python3
"""Guard target-specific dispatch between Koronos bootstrap tasks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "kernel/core/koronos.cpp").read_text(encoding="utf-8")


class TargetInitRoutingTests(unittest.TestCase):
    def test_live_task_only_launches_live_target(self):
        live = SOURCE.split("static void task_live(void *)", 1)[1].split(
            "static void task_recovery(void *)", 1
        )[0]
        self.assertIn('module_cmdline_selects_target(user_init, "live")', live)
        self.assertIn("koronos_launch_selected_userspace()", live)

    def test_installer_task_launches_installer_target_elf(self):
        installer = SOURCE.split("static void task_installer(void *)", 1)[1].split(
            "static const char *task_state_name", 1
        )[0]
        self.assertIn('module_cmdline_selects_target(user_init, "installer")', installer)
        self.assertIn("koronos_launch_selected_userspace()", installer)
        self.assertIn("USERSPACE HANDOFF NOT VERIFIED", installer)

    def test_installer_does_not_claim_unstarted_services_are_running(self):
        self.assertNotIn("Hardware discovery service started", SOURCE)
        self.assertNotIn("Storage discovery service started", SOURCE)
        self.assertNotIn("Initializing installer services in parallel", SOURCE)

    def test_target_matching_requires_complete_token(self):
        helper = SOURCE.split("static bool module_cmdline_selects_target", 1)[1].split(
            "static void task_console", 1
        )[0]
        self.assertIn("target=", helper)
        self.assertIn("*b == 0 || *b == ' '", helper)


if __name__ == "__main__":
    unittest.main()
