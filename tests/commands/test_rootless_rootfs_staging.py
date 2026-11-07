#!/usr/bin/env python3
"""Test that live rootfs staging works without privileged chroot access."""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
busybox_script = ROOT / "tools/commands/install-busybox-applets.sh"
native_tools = (ROOT / "tools/commands/build-chimera-native-tools.sh").read_text(encoding="utf-8")

assert "chroot " not in busybox_script.read_text(encoding="utf-8")
assert "chroot " not in native_tools
assert 'rootfs_has_executable java' in native_tools
assert 'rootfs_has_executable terminald' in native_tools

with tempfile.TemporaryDirectory() as tmp:
    rootfs = Path(tmp) / "rootfs"
    (rootfs / "bin").mkdir(parents=True)
    busybox = rootfs / "bin/busybox"
    busybox.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--list\" ]; then printf 'sh\\necho\\nls\\n'; fi\n",
        encoding="utf-8",
    )
    busybox.chmod(0o755)
    (rootfs / "bin/sh").symlink_to("busybox")
    (rootfs / "bin/echo").symlink_to("busybox")
    subprocess.run(["bash", str(busybox_script), str(rootfs)], check=True)
    assert (rootfs / "usr/local/bin/ls").is_symlink()
    manifest = (rootfs / "usr/share/chimera/commands/busybox-applets.tsv").read_text()
    assert "echo|/bin/echo|busybox-static" in manifest
    assert "ls|/usr/local/bin/ls|busybox-static" in manifest
print("PASS: BusyBox applets are resolved from target-rootfs paths without chroot.")
