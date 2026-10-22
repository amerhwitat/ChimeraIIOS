import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\n"
ENTRY = "USER INIT SYSCALL: target={target} init_pid={pid}\n"
READY = "USERSPACE READY: target={target} init_pid={pid}\n"


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

    def test_readiness_marker_without_user_entry_ack_is_rejected(self):
        result = run("live", KERNEL + READY.format(target="live", pid=1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_requires_matching_target(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("requested target=installer", result.stdout)

    def test_requires_same_pid_for_entry_and_ready(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=2)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_requires_ordered_markers(self):
        trace = READY.format(target="live", pid=1) + ENTRY.format(target="live", pid=1) + KERNEL
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_live_with_user_originated_syscall_and_matching_pid(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        self.assertEqual(run("live", trace).returncode, 0)

    def test_rejects_zero_or_mismatched_pid(self):
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)).returncode, 1)
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="recovery", pid=0) + READY.format(target="recovery", pid=0)).returncode, 1)

    def test_accepts_recovery_with_nonzero_pid(self):
        trace = KERNEL + ENTRY.format(target="recovery", pid=2) + READY.format(target="recovery", pid=2)
        self.assertEqual(run("recovery", trace).returncode, 0)

    def test_distinguishes_cpl3_entry_from_blocked_service_readiness(self):
        trace = KERNEL + ENTRY.format(target="recovery", pid=1) + "NATIVE INIT BLOCKED: storage unavailable\n"
        result = run("recovery", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CPL 3 init entry observed", result.stdout)
        self.assertIn("services are unavailable", result.stdout)

    def test_entry_without_readiness_or_block_reason_is_diagnostic_not_pass(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1)
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("inspect init exit and service diagnostics", result.stdout)


if __name__ == "__main__":
    unittest.main()
