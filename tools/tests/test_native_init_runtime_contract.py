#!/usr/bin/env python3
"""Contract tests for real ring-3 rootfs and tmpfs operations in native init."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NativeInitRuntimeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT / "kernel/userspace/native_init.c").read_text()
        cls.builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()

    def test_tmpfs_selftest_proves_truncate_after_write_and_read(self):
        start = self.native.index("static int vfs_selftest(void)")
        end = self.native.index("static int os_release_selftest(void)", start)
        body = self.native[start:end]
        self.assertIn('"/tmp/.chimera-vfs-selftest"', body)
        self.assertIn("0x0502L", body)  # O_CREAT | O_TRUNC | O_RDWR
        self.assertIn("0x0402L", body)  # reopen with O_TRUNC | O_RDWR
        self.assertIn("call3(8, truncated_fd, (long)observed, 1) != 0", body)
        self.assertIn("USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE", self.native)

    def test_os_release_is_opened_read_and_closed_from_ring3(self):
        start = self.native.index("static int os_release_selftest(void)")
        end = self.native.index("static long write_console", start)
        body = self.native[start:end]
        self.assertIn('"/etc/os-release"', body)
        self.assertIn("open_readonly(path)", body)
        self.assertIn("call3(8, fd, (long)observed", body)
        self.assertIn("call1(18, fd)", body)
        self.assertIn("USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE", self.native)

    def test_live_and_recovery_initramfs_include_os_release(self):
        self.assertIn('> "$INIT/etc/os-release"', self.builder)
        self.assertIn('> "$REC/etc/os-release"', self.builder)
        self.assertIn("NAME=ChimeraIIOS", self.builder)
        self.assertIn("NAME=ChimeraIIOS Recovery", self.builder)
        self.assertLess(self.builder.index('cp -a "$INIT/." "$REC/"'), self.builder.index("NAME=ChimeraIIOS Recovery"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
