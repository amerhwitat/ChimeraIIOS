#!/usr/bin/env python3
"""Fail-closed contract for target-specific GUI entrypoint resolution."""
from pathlib import Path
root = Path(__file__).resolve().parents[2]
source = (root / "kernel/userspace/native_init.c").read_text(encoding="utf-8")
builder = (root / "tools/build-production-init-elfs.sh").read_text(encoding="utf-8")
expected = {
    1: ("aurora-session", "/usr/bin/aurora-session"),
    2: ("install-executor", "/usr/bin/chimera-installer"),
    3: ("recovery-runtime", "/usr/bin/chimera-recovery"),
}
for target_id, (component, path) in expected.items():
    assert f"#if CHIMERA_INIT_TARGET_ID == {target_id}" in source or f"#elif CHIMERA_INIT_TARGET_ID == {target_id}" in source
    assert f'#define CHIMERA_GUI_COMPONENT "{component}"' in source
    assert f'#define CHIMERA_GUI_ENTRYPOINT "{path}"' in source
    assert f"{component}" in source
assert 'target_id=1' in builder and 'target_id=2' in builder and 'target_id=3' in builder
assert '-DCHIMERA_INIT_TARGET_ID="$target_id"' in builder
assert 'open_readonly(CHIMERA_GUI_ENTRYPOINT)' in source
assert 'NATIVE INIT GUI ENTRYPOINT MISSING' in source
assert 'EXECVE/GRAPHICS BACKEND IS UNAVAILABLE' in source
assert 'call1(1, 78)' in source
# A component lookup is explicitly not a readiness claim.
assert 'USERSPACE TARGET READY:' not in source
print("PASS: Live/Installer/Recovery GUI entrypoint mapping is target-specific and fails closed.")
