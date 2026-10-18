import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).with_name("verify-userspace-handoff.py")
def run(target,trace):
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/"trace.log"
        log.write_text(trace,encoding="utf-8")
        return subprocess.run([sys.executable,str(SCRIPT),target,str(log)],capture_output=True,text=True)

class UserspaceHandoffVerifierTests(unittest.TestCase):
    def test_kernel_ready_alone_is_not_userspace_ready(self):
        result=run("live","[KRN ] KORONOS READY\n")
        self.assertEqual(result.returncode,1)
        self.assertIn("actual init PID readiness marker",result.stdout)
    def test_requires_matching_target(self):
        result=run("installer","[KRN ] KORONOS READY\nUSERSPACE READY: target=live init_pid=1\n")
        self.assertEqual(result.returncode,1)
        self.assertIn("installer userspace readiness with nonzero init PID",result.stdout)
    def test_accepts_live_with_nonzero_pid(self):
        self.assertEqual(run("live","[KRN ] KORONOS READY\nUSERSPACE READY: target=live init_pid=1\n").returncode,0)
    def test_rejects_zero_or_mismatched_pid(self):
        self.assertEqual(run("recovery","[KRN ] KORONOS READY\nUSERSPACE READY: target=live init_pid=1\n").returncode,1)
        self.assertEqual(run("recovery","[KRN ] KORONOS READY\nUSERSPACE READY: target=recovery init_pid=0\n").returncode,1)
    def test_accepts_recovery_with_nonzero_pid(self):
        self.assertEqual(run("recovery","[KRN ] KORONOS READY\nUSERSPACE READY: target=recovery init_pid=2\n").returncode,0)
if __name__=="__main__":unittest.main()
