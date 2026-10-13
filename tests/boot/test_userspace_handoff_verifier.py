from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\n"
INIT = "[USER] Ring-3 Chimera init entered successfully; userspace handoff verified\n"

def run(tmp_path, target, trace):
    log = tmp_path / "trace.log"
    log.write_text(trace, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), target, str(log)], capture_output=True, text=True)

def test_kernel_ready_alone_is_not_userspace_ready(tmp_path):
    result = run(tmp_path, "live", KERNEL)
    assert result.returncode == 1
    assert "native init ELF ring-3 execution marker" in result.stdout

def test_kernel_marker_and_init_marker_are_not_target_ready(tmp_path):
    result = run(tmp_path, "installer", KERNEL + INIT + "USERSPACE READY: live\n")
    assert result.returncode == 1
    assert "installer userspace readiness marker" in result.stdout

def test_accepts_complete_live_trace(tmp_path):
    result = run(tmp_path, "live", KERNEL + INIT + "USERSPACE READY: live\n")
    assert result.returncode == 0
