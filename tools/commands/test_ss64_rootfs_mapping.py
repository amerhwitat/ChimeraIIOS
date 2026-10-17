#!/usr/bin/env python3
"""Tests for SS64 Linux command path staging."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("crawl_ss64.py")
SPEC = importlib.util.spec_from_file_location("crawl_ss64", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SS64RootfsMappingTests(unittest.TestCase):
    def test_every_valid_name_is_visible_in_bin_and_sbin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "usr/bin").mkdir(parents=True)
            (root / "usr/bin/ls").write_text("provider", encoding="utf-8")
            counts = MODULE.install_command_path_aliases(
                root, ["ls", "grep", "Get-Process", "bad/name", "../escape", ""]
            )
            self.assertEqual(counts, {"bin": 3, "sbin": 3})
            for directory in ("bin", "sbin"):
                for name in ("ls", "grep", "Get-Process"):
                    link = root / directory / name
                    self.assertTrue(link.is_symlink(), str(link))
                    self.assertEqual(os.readlink(link), "../usr/bin/" + name)
                    self.assertEqual(link.resolve(), (root / "usr/bin" / name).resolve())
                self.assertFalse((root / directory / "bad/name").exists())
                self.assertFalse((root / directory / "../escape").exists())

    def test_preserves_existing_files_and_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bin").mkdir()
            (root / "sbin").mkdir()
            (root / "usr/bin").mkdir(parents=True)
            existing = root / "bin/ls"
            existing.write_text("administrator binary", encoding="utf-8")
            existing.chmod(0o755)
            existing_sbin = root / "sbin/grep"
            existing_sbin.symlink_to("../usr/bin/grep")
            counts = MODULE.install_command_path_aliases(root, ["ls", "grep"])
            self.assertEqual(counts, {"bin": 1, "sbin": 1})
            self.assertEqual(existing.read_text(encoding="utf-8"), "administrator binary")
            self.assertEqual(os.readlink(existing_sbin), "../usr/bin/grep")

    def test_merged_usr_symlink_layout_uses_valid_relative_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "usr/bin").mkdir(parents=True)
            (root / "usr/sbin").mkdir(parents=True)
            (root / "usr/bin/ls").write_text("provider", encoding="utf-8")
            (root / "usr/bin/grep").write_text("dispatcher shim", encoding="utf-8")
            (root / "bin").symlink_to("usr/bin")
            (root / "sbin").symlink_to("usr/sbin")
            counts = MODULE.install_command_path_aliases(root, ["ls", "grep"])
            self.assertEqual(counts, {"bin": 0, "sbin": 2})
            self.assertEqual((root / "bin/ls").resolve(), (root / "usr/bin/ls").resolve())
            self.assertEqual((root / "sbin/ls").resolve(), (root / "usr/bin/ls").resolve())
            self.assertEqual((root / "sbin/grep").resolve(), (root / "usr/bin/grep").resolve())
            self.assertEqual(os.readlink(root / "usr/sbin/ls"), "../bin/ls")
            self.assertEqual(os.readlink(root / "usr/sbin/grep"), "../bin/grep")

    def test_does_not_treat_dispatcher_shim_as_real_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "usr/bin").mkdir(parents=True)
            (root / "usr/bin/chimera-compat").write_text("# dispatcher", encoding="utf-8")
            (root / "usr/bin/chimera-compat").chmod(0o755)
            (root / "usr/bin/grep").symlink_to("chimera-compat")
            self.assertIsNone(MODULE.rootfs_provider(root, "grep"))


if __name__ == "__main__":
    unittest.main()
