#!/usr/bin/env python3
"""Guard target init against mixing Chimera IDs with Linux SYSCALL numbers."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPERS = ROOT / "kernel/targets/init_common.h"
COMPAT = ROOT / "kernel/core/compat.cpp"
TARGETS = (
    ROOT / "kernel/targets/live_init.c",
    ROOT / "kernel/targets/installer_init.c",
    ROOT / "kernel/targets/recovery_init.c",
)


class TargetInitSyscallAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = HELPERS.read_text(encoding="utf-8")
        cls.compat = COMPAT.read_text(encoding="utf-8")

    def test_payload_uses_linux_x86_64_numbers_translated_by_koronos(self):
        for macro, number in (
            ("LINUX_X64_SYS_WRITE", 1),
            ("LINUX_X64_SYS_GETPID", 39),
            ("LINUX_X64_SYS_EXIT", 60),
        ):
            with self.subTest(macro=macro):
                self.assertIn(f"#define {macro} {number}", self.helpers)
        for linux_number, canonical in ((1, 9), (39, 2), (60, 1)):
            with self.subTest(linux_number=linux_number):
                self.assertIn(
                    f"case {linux_number}: return {canonical};", self.compat
                )

    def test_targets_only_use_implemented_init_operations(self):
        for path in TARGETS:
            source = path.read_text(encoding="utf-8")
            with self.subTest(target=path.name):
                self.assertIn("init_int80();", source)
                self.assertIn("init_getpid()", source)
                self.assertIn("init_emit_readiness(pid);", source)
                self.assertIn("init_exit(0);", source)
                self.assertNotIn("init_yield(", source)
                self.assertNotIn("init_time_ticks(", source)


if __name__ == "__main__":
    unittest.main()
