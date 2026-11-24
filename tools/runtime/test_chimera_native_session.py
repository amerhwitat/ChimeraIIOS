#!/usr/bin/env python3
"""Tests for native session preflight, evidence semantics and harness labelling."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/runtime/chimera-native-session.py"
SESSIONS = ("aurora", "marine", "freexp", "freewin11")

COMPOSITOR_STUB = r"""
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(void) {
  const char *d = getenv("XDG_RUNTIME_DIR");
  char path[4096];
  if (!d) return 3;
  snprintf(path, sizeof(path), "%s/wayland-0", d);
  int fd = socket(AF_UNIX, SOCK_STREAM, 0);
  if (fd < 0) return 4;
  struct sockaddr_un addr;
  memset(&addr, 0, sizeof(addr));
  addr.sun_family = AF_UNIX;
  strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);
  if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) return 5;
  listen(fd, 1);
  for (;;) pause();
}
"""

SHELL_STUB = r"""
#include <unistd.h>
int main(int argc, char **argv) { (void)argc; (void)argv; for (;;) pause(); }
"""


def run(*args: str, expect: int = 0) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"session script returned {proc.returncode} (expected {expect})\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chimera-native-session-test-") as tmp:
        work = Path(tmp)
        empty_rootfs = work / "empty-rootfs"
        empty_rootfs.mkdir()
        import hashlib

        run("--session", "not-a-session", expect=2)

        for session in SESSIONS:
            manifest = ROOT / "desktop/sessions" / f"{session}.json"
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            output = work / f"{session}-preflight.json"
            summary = run(
                "--session", session, "--rootfs", str(empty_rootfs),
                "--preflight-only", "--output", str(output), expect=78,
            )
            evidence = json.loads(output.read_text(encoding="utf-8"))
            assert summary["status"] == "blocked"
            assert evidence["session"] == session
            assert evidence["manifest"]["sha256"] == manifest_sha
            assert evidence["session_ready"] is False
            assert evidence["koronos_native_boot_verified"] is False
            assert evidence["production_acceptance"] is False
            assert evidence["conformance_claim"] is False
            assert evidence["missing"], "blocked preflight must list missing pieces"
            assert any("shell binary" in item for item in evidence["missing"])
            assert any("display server" in item for item in evidence["missing"])
            assert any("input event devices" in item for item in evidence["missing"])

        compiler = shutil.which("cc")
        if not compiler:
            print("harness process test SKIPPED: no C compiler", file=sys.stderr)
            print("native session tests: PASS (preflight only)")
            return 0

        compositor = work / "compositor-stub"
        shell = work / "shell-stub"
        for source, target in ((COMPOSITOR_STUB, compositor), (SHELL_STUB, shell)):
            source_file = work / f"{target.name}.c"
            source_file.write_text(source, encoding="utf-8")
            subprocess.run([compiler, "-O2", str(source_file), "-o", str(target)],
                           check=True)

        runtime = work / "runtime"
        input_dir = work / "input"
        input_dir.mkdir()
        (input_dir / "event0").write_text("synthetic", encoding="utf-8")
        evidence_path = work / "harness-evidence.json"

        summary = run(
            "--session", "aurora", "--mode", "native", "--harness",
            "--runtime-dir", str(runtime), "--input-dir", str(input_dir),
            "--compositor", str(compositor), "--shell", str(shell),
            "--timeout", "5", "--hold", "0.2", "--output", str(evidence_path),
            expect=1,
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert summary["status"] == "harness-checks-satisfied", summary
        assert evidence["synthetic_harness"] is True
        assert evidence["checks_satisfied"] is True
        assert evidence["checks"]["graphics_surface_observed"] is True
        assert evidence["checks"]["input_devices_observed"] is True
        assert evidence["checks"]["compositor_process_observed"] is True
        assert evidence["checks"]["shell_process_observed"] is True
        assert evidence["processes"]["display_server"]["pid"]
        assert evidence["processes"]["shell"]["pid"]
        assert evidence["input"]["device_count"] == 1
        assert evidence["session_ready"] is False
        assert evidence["koronos_native_boot_verified"] is False
        assert evidence["production_acceptance"] is False
        assert evidence["status"] == "harness-checks-satisfied"

    print("native session tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
