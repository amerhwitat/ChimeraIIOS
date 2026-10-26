#!/usr/bin/env python3
"""Unit tests for strict production ISO QEMU matrix evidence parsing."""
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = runpy.run_path(str(ROOT / "tools/run-production-qemu-matrix.py"), run_name="matrix_test")
target_marker_errors = MATRIX["target_marker_errors"]
target_key_commands = MATRIX["target_key_commands"]


class ProductionQemuMatrixContract(unittest.TestCase):
    def test_matrix_never_claims_full_production_acceptance(self):
        source = (ROOT / "tools/run-production-qemu-matrix.py").read_text()
        self.assertIn('"production_acceptance": "NOT ESTABLISHED BY THIS MATRIX"', source)
        self.assertIn('"target_boot_matrix":', source)
        self.assertIn('"qemu_started": process is not None', source)
        self.assertIn('"qemu_started": False', source)

    def test_target_selection_resets_grub_menu_before_navigation(self):
        self.assertEqual(target_key_commands("live"), ["sendkey home", "sendkey ret"])
        self.assertEqual(
            target_key_commands("installer"),
            ["sendkey home", "sendkey down", "sendkey down", "sendkey ret"],
        )
        self.assertEqual(
            target_key_commands("recovery"),
            ["sendkey home", "sendkey down", "sendkey down", "sendkey down",
             "sendkey down", "sendkey down", "sendkey down", "sendkey down",
             "sendkey down", "sendkey ret"],
        )
        with self.assertRaises(ValueError):
            target_key_commands("unknown")

    def test_target_indices_match_top_level_grub_boot_entries(self):
        import re

        grub = (ROOT / "boot/iso/grub.cfg").read_text()
        ids = re.findall(r'^menuentry ".*?" --id ([A-Za-z0-9_-]+) \{', grub, re.M)
        self.assertEqual(ids[0], "aurora-live")
        self.assertEqual(ids[2], "install")
        self.assertEqual(ids[5], "recovery")  # nested menu; do not select for matrix
        self.assertEqual(ids[8], "diagnostics")  # direct recovery initramfs boot
        self.assertEqual(MATRIX["TARGETS"], {"live": 0, "installer": 2, "recovery": 8})
        diagnostics = grub.split('menuentry "Chimera II OS — Diagnostics [progress]" --id diagnostics {', 1)[1].split('menuentry "Chimera II OS — Retro Computer Center" --id retro {', 1)[0]
        self.assertIn("chm.progress=events target=recovery", diagnostics)
        self.assertIn("/boot/recovery/user-init-recovery.elf", diagnostics)
        self.assertNotIn("/boot/live/user-init-live.elf", diagnostics)
        self.assertEqual(diagnostics.count("chimera-user-init-elf"), 1)

    def test_every_direct_grub_boot_has_one_target_matched_native_init(self):
        grub = (ROOT / "boot/iso/grub.cfg").read_text()
        entries = re.split(r'(?=^menuentry )', grub, flags=re.M)
        checked = 0
        for entry in entries:
            kernel = re.search(r'^\\s*multiboot2 .*? target=(live|installer|recovery)(?:\\s|$)', entry, re.M)
            if not kernel:
                continue
            target = kernel.group(1)
            init_modules = re.findall(
                r'^\\s*module2 .*?chimera-user-init-elf target=(live|installer|recovery)\\s*        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=live init_pid=12
NATIVE INIT PID: target=live pid=12
USERSPACE ROOTFS MOUNTED: target=live root=read-only tmpfs=/tmp
NATIVE INIT VFS SELFTEST PASS: create/write/seek/read/close verified
USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE
USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE
USERSPACE TARGET READY: live component=aurora-session init pid=12
"""
        self.assertEqual(target_marker_errors("live", trace), [])

    def test_probe_readiness_without_target_health_is_rejected(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=live init_pid=1
NATIVE INIT PID: target=live pid=1
NATIVE INIT VFS SELFTEST PASS
"""
        errors = target_marker_errors("live", trace)
        self.assertTrue(any("target-specific production readiness" in x for x in errors))
        self.assertTrue(any("/etc/os-release" in x for x in errors))
        self.assertTrue(any("writable /tmp" in x for x in errors))

    def test_pid_mismatch_and_explicit_blocked_init_fail(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=installer init_pid=1
NATIVE INIT PID: target=installer pid=2
NATIVE INIT VFS SELFTEST PASS
/install marker open/read/close
/tmp write selftest PASS
USERSPACE TARGET READY: installer component=install-executor init pid=1
NATIVE INIT BLOCKED: services unavailable
"""
        errors = target_marker_errors("installer", trace)
        self.assertTrue(any("PID differ" in x for x in errors))
        self.assertTrue(any("explicitly reported blocked" in x for x in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
,
                entry, re.M
            )
            self.assertEqual(init_modules, [target], entry.splitlines()[0])
            checked += 1
        self.assertGreater(checked, 0)

    def test_matching_real_runtime_markers_are_accepted_by_parser(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=live init_pid=12
NATIVE INIT PID: target=live pid=12
USERSPACE ROOTFS MOUNTED: target=live root=read-only tmpfs=/tmp
NATIVE INIT VFS SELFTEST PASS: create/write/seek/read/close verified
USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE
USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE
USERSPACE TARGET READY: live component=aurora-session init pid=12
"""
        self.assertEqual(target_marker_errors("live", trace), [])

    def test_probe_readiness_without_target_health_is_rejected(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=live init_pid=1
NATIVE INIT PID: target=live pid=1
NATIVE INIT VFS SELFTEST PASS
"""
        errors = target_marker_errors("live", trace)
        self.assertTrue(any("target-specific production readiness" in x for x in errors))
        self.assertTrue(any("/etc/os-release" in x for x in errors))
        self.assertTrue(any("writable /tmp" in x for x in errors))

    def test_pid_mismatch_and_explicit_blocked_init_fail(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=installer init_pid=1
NATIVE INIT PID: target=installer pid=2
NATIVE INIT VFS SELFTEST PASS
/install marker open/read/close
/tmp write selftest PASS
USERSPACE TARGET READY: installer component=install-executor init pid=1
NATIVE INIT BLOCKED: services unavailable
"""
        errors = target_marker_errors("installer", trace)
        self.assertTrue(any("PID differ" in x for x in errors))
        self.assertTrue(any("explicitly reported blocked" in x for x in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
