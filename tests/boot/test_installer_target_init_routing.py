#!/usr/bin/env python3
"""Guard target-specific dispatch between Koronos bootstrap tasks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "kernel/core/koronos.cpp").read_text(encoding="utf-8")
LAUNCHER = (ROOT / "kernel/core/target_launch.cpp").read_text(encoding="utf-8")
ELF_VERIFIER = (ROOT / "scripts/kbuild/verify.py").read_text(encoding="utf-8")


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
        self.assertIn("target-init-installer.elf is missing", installer)

    def test_recovery_task_launches_recovery_target_elf(self):
        recovery = SOURCE.split("static void task_recovery(void *)", 1)[1].split(
            "static void task_installer(void *)", 1
        )[0]
        self.assertIn('module_cmdline_selects_target(user_init, "recovery")', recovery)
        self.assertIn("koronos_launch_selected_userspace()", recovery)

    def test_installer_fails_instead_of_waiting_when_target_init_is_missing(self):
        installer = SOURCE.split("static void task_installer(void *)", 1)[1].split(
            "static const char *task_state_name", 1
        )[0]
        self.assertIn("if (!user_init)", installer)
        self.assertIn("target-init-installer.elf is missing", installer)
        self.assertIn("Refusing to wait", installer)
        self.assertNotIn("Waiting for the Koronos userspace installer loader", installer)

    def test_launcher_does_not_treat_missing_init_as_success(self):
        self.assertIn("no USER_INIT_ELF Multiboot2 module was supplied", LAUNCHER)
        self.assertNotIn("if (count==0) return 0", LAUNCHER)
        self.assertIn("attempted=true", LAUNCHER)

    def test_elf_verifier_requires_the_new_installer_dispatch_contract(self):
        self.assertIn("[INST] Installer image, manifest and contract verified as present", ELF_VERIFIER)
        self.assertIn("[INST] Dispatching the target-specific installer init ELF", ELF_VERIFIER)
        self.assertIn("target-init-installer.elf is missing", ELF_VERIFIER)
        self.assertNotIn("[INST] Installer runtime initialization", ELF_VERIFIER)

    def test_installer_does_not_claim_unstarted_services_are_running(self):
        self.assertNotIn("Hardware discovery service started", SOURCE)
        self.assertNotIn("Storage discovery service started", SOURCE)
        self.assertNotIn("Initializing installer services in parallel", SOURCE)

    def test_monitor_does_not_label_scheduler_callbacks_as_processes(self):
        self.assertIn('console_raw("[TASK] id=")', SOURCE)
        self.assertIn('console_write("[MON ] Registered process contexts: ")', SOURCE)
        self.assertNotIn('console_raw("[PROC] id=")', SOURCE)

    def test_target_matching_requires_complete_token(self):
        helper = SOURCE.split("static bool module_cmdline_selects_target", 1)[1].split(
            "static void task_console", 1
        )[0]
        self.assertIn("target=", helper)
        self.assertIn("*b == 0 || *b == ' '", helper)


if __name__ == "__main__":
    unittest.main()
