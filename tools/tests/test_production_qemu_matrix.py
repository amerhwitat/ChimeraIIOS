#!/usr/bin/env python3
"""Unit tests for strict production ISO QEMU matrix evidence parsing."""
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = runpy.run_path(str(ROOT / "tools/run-production-qemu-matrix.py"), run_name="matrix_test")
target_marker_errors = MATRIX["target_marker_errors"]


class ProductionQemuMatrixContract(unittest.TestCase):
    def test_matching_real_runtime_markers_are_accepted_by_parser(self):
        trace = """[KRN ] KORONOS READY
USER INIT SYSCALL: target=live init_pid=12
NATIVE INIT PID: target=live pid=12
NATIVE INIT VFS SELFTEST PASS: create/write/seek/read/close verified
/etc/os-release open/read/close verified
/tmp write selftest PASS
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
