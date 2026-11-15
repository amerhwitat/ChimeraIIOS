import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\\n"
ENTRY = "USER INIT SYSCALL: target={target} init_pid={pid}\\n"
READY = "USERSPACE READY: target={target} init_pid={pid}\\n"
ACTIVE = "KORONOS PID1 ACTIVE: target={target} init_pid={pid}\\n"
EXITED = "[RUN ] Target userspace init emitted its own readiness handshake and exited cleanly\\n"


def run(target, trace):
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "trace.log"
        log.write_text(trace, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), target, str(log)],
                              capture_output=True, text=True)


class PersistentTargetPid1SourceTests(unittest.TestCase):
    def test_all_three_target_inits_remain_resident_after_readiness(self):
        root = Path(__file__).resolve().parents[2]
        for target in ("live", "installer", "recovery"):
            with self.subTest(target=target):
                source = (root / "kernel/targets" / f"{target}_init.c").read_text(encoding="utf-8")
                self.assertIn("init_pid1_wait();", source)
                self.assertNotIn("init_exit(0);", source)

    def test_kernel_active_marker_requires_running_process_and_disarms_startup_deadline(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "kernel/core/target_launch.cpp").read_text(encoding="utf-8")
        self.assertIn("current.state != CHIMERA_PROCESS_RUNNING", source)
        self.assertIn("koronos_user_timeout_disarm();", source)
        self.assertIn("log_pid1_active(static_cast<Target>(active_target), active_pid);", source)

    def test_user_readiness_is_logged_before_kernel_pid1_active_record(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "kernel/core/koronos.cpp").read_text(encoding="utf-8")
        user_bytes = source.index("for (uint64_t i = 0; i < length; ++i) debugcon_write8(bytes[i]);")
        active_check = source.index("koronos_target_note_user_write(reinterpret_cast<const char *>(bytes), length)")
        self.assertLess(user_bytes, active_check)


class UserspaceHandoffVerifierTests(unittest.TestCase):
    def test_kernel_ready_alone_is_not_userspace_ready(self):
        result = run("live", KERNEL)
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_readiness_marker_without_user_entry_ack_is_rejected(self):
        result = run("live", KERNEL + READY.format(target="live", pid=1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_rejects_readiness_without_persistent_pid1_evidence(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("persistent PID 1 active marker", result.stdout)

    def test_rejects_init_that_exits_after_readiness(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1) + EXITED)
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("PID 1 terminated or was aborted", result.stdout)

    def test_requires_matching_target(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1))
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("persistent PID1-active markers", result.stdout)

    def test_requires_same_pid_for_entry_ready_and_active(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=2))
        self.assertEqual(run("live", trace).returncode, 1)

    def test_requires_ordered_markers(self):
        trace = (ACTIVE.format(target="live", pid=1) + READY.format(target="live", pid=1)
                 + ENTRY.format(target="live", pid=1) + KERNEL)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_persistent_live_pid1(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1))
        result = run("live", trace)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("persistent PID 1", result.stdout)

    def test_accepts_persistent_recovery_pid1_with_nonzero_pid(self):
        trace = (KERNEL + ENTRY.format(target="recovery", pid=2)
                 + READY.format(target="recovery", pid=2) + ACTIVE.format(target="recovery", pid=2))
        self.assertEqual(run("recovery", trace).returncode, 0)

    def test_rejects_zero_or_mismatched_pid(self):
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="live", pid=1)
                             + READY.format(target="live", pid=1)
                             + ACTIVE.format(target="live", pid=1)).returncode, 1)
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="recovery", pid=0)
                             + READY.format(target="recovery", pid=0)
                             + ACTIVE.format(target="recovery", pid=0)).returncode, 1)


if __name__ == "__main__":
    unittest.main()
