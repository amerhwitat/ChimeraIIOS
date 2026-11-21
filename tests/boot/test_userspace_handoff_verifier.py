import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\n"
ENTRY = "USER INIT SYSCALL: target={target} init_pid={pid}\n"
READY = "USERSPACE READY: target={target} init_pid={pid}\n"
ACTIVE = "KORONOS PID1 ACTIVE: target={target} init_pid={pid}\n"

def run(target, trace):
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "trace.log"
        log.write_text(trace, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), target, str(log)], capture_output=True, text=True)

class UserspaceHandoffVerifierTests(unittest.TestCase):
    def test_kernel_ready_alone_is_not_userspace_ready(self):
        result = run("live", KERNEL)
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_readiness_without_cpl3_ack_is_rejected(self):
        result = run("live", KERNEL + READY.format(target="live", pid=1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_requires_matching_target(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1)
        self.assertEqual(run("installer", trace).returncode, 1)

    def test_requires_same_pid_across_all_markers(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=2) + ACTIVE.format(target="live", pid=1)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_requires_marker_order(self):
        trace = ACTIVE.format(target="live", pid=1) + READY.format(target="live", pid=1) + ENTRY.format(target="live", pid=1) + KERNEL
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_persistent_live_pid1(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1)
        result = run("live", trace)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_readiness_without_active_marker(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_persistent_recovery_pid1(self):
        trace = KERNEL + ENTRY.format(target="recovery", pid=2) + READY.format(target="recovery", pid=2) + ACTIVE.format(target="recovery", pid=2)
        self.assertEqual(run("recovery", trace).returncode, 0)

    def test_rejects_exit_after_active_marker(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1) + "Target userspace init emitted its own readiness handshake and exited cleanly\n"
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("terminated or was aborted", result.stdout)

    def test_rejects_runtime_error_after_active_marker(self):
        trace = KERNEL + ENTRY.format(target="installer", pid=1) + READY.format(target="installer", pid=1) + ACTIVE.format(target="installer", pid=1) + "[RUN ] ERROR: scheduler failure\n"
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("terminated or was aborted", result.stdout)

    def test_rejects_kernel_panic_after_active_marker(self):
        trace = KERNEL + ENTRY.format(target="recovery", pid=3) + READY.format(target="recovery", pid=3) + ACTIVE.format(target="recovery", pid=3) + "KORONOS PANIC: page fault\n"
        self.assertEqual(run("recovery", trace).returncode, 1)

    def test_all_target_init_sources_wait_instead_of_exiting(self):
        root = Path(__file__).resolve().parents[2]
        for target in ("live", "installer", "recovery"):
            with self.subTest(target=target):
                source = (root / "kernel/targets" / (target + "_init.c")).read_text(encoding="utf-8")
                self.assertIn("init_pid1_wait();", source)
                self.assertNotIn("init_exit(0);", source)

if __name__ == "__main__":
    unittest.main()
