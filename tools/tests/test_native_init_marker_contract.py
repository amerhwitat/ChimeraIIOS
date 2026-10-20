#!/usr/bin/env python3
"""Guard the kernel/probe/full-ISO readiness marker contract against drift."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / "kernel/core/target_launch.cpp"
PROBE = ROOT / "kernel/tests/user_init_smoke.c"
VERIFY = ROOT / "tests/migration/verify-userspace-handoff.py"
ACCEPTANCE = ROOT / ".github/workflows/koronos-userspace-acceptance.yml"


class NativeInitMarkerContractTests(unittest.TestCase):
    def test_kernel_parser_and_probe_use_canonical_marker(self):
        launch = LAUNCH.read_text(encoding="utf-8")
        probe = PROBE.read_text(encoding="utf-8")
        self.assertIn('const char *a="USERSPACE READY: target=";', launch)
        self.assertIn('const char *b=" init_pid=";', launch)
        self.assertIn('"USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid="', probe)
        self.assertNotIn('const char *a="USERSPACE READY: ";', launch)
        self.assertNotIn('"USERSPACE READY: " CHIMERA_TARGET_NAME " init pid="', probe)

    def test_ci_and_authoritative_verifier_match(self):
        workflow = ACCEPTANCE.read_text(encoding="utf-8")
        verifier = VERIFY.read_text(encoding="utf-8")
        self.assertIn('USERSPACE READY: target=${TARGET} init_pid=[1-9][0-9]*', workflow)
        self.assertIn('! grep -Fq "USERSPACE READY: target=live" "$LOG"', workflow)
        self.assertIn(r'USERSPACE READY: target=(live|installer|recovery) init_pid=', verifier)
        self.assertNotIn('USERSPACE READY: ${TARGET} init pid=', workflow)


if __name__ == "__main__":
    unittest.main()
