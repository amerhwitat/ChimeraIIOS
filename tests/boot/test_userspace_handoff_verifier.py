import importlib.util
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")

def run(tmp_path, target, trace):
    log = tmp_path / "trace.log"
    log.write_text(trace, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), target, str(log)], capture_output=True, text=True)

def test_kernel_ready_alone_is_not_userspace_ready(tmp_path):
    result = run(tmp_path, "live", "[KRN ] KORONOS READY\n")
    assert result.returncode == 1
    assert "actual init PID readiness marker" in result.stdout

def test_requires_target_specific_ready_marker(tmp_path):
    result = run(tmp_path, "installer", "[KRN ] KORONOS READY\nUSERSPACE READY: init pid=1\nUSERSPACE READY: live\n")
    assert result.returncode == 1
    assert "installer userspace readiness marker" in result.stdout

def test_accepts_complete_live_trace(tmp_path):
    result = run(tmp_path, "live", "[KRN ] KORONOS READY\nUSERSPACE READY: init pid=1\nUSERSPACE READY: live\n")
    assert result.returncode == 0

def test_rejects_zero_or_mismatched_init_pid(tmp_path):
    result = run(tmp_path, "recovery", "[KRN ] KORONOS READY\\nUSERSPACE READY: target=live init_pid=1\\n")
    assert result.returncode == 1
    result = run(tmp_path, "recovery", "[KRN ] KORONOS READY\\nUSERSPACE READY: target=recovery init_pid=0\\n")
    assert result.returncode == 1

def test_accepts_target_specific_nonzero_init_pid(tmp_path):
    result = run(tmp_path, "recovery", "[KRN ] KORONOS READY\\nUSERSPACE READY: target=recovery init_pid=2\\n")
    assert result.returncode == 0
