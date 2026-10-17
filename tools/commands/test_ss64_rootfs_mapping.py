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
            self.assertEqual(MODULE.validate_command_path_aliases(
                root, ["ls", "grep", "Get-Process", "bad/name", "../escape", ""]
            ), 3)
            for directory in ("bin", "sbin"):
                for name in ("ls", "grep", "Get-Process"):
                    link = root / directory / name
                    self.assertTrue(link.is_symlink(), str(link))
                    self.assertEqual(os.readlink(link), "../usr/bin/" + name)
                    self.assertEqual(link.resolve(), (root / "usr/bin" / name).resolve())
                self.assertFalse((root / directory / "bad/name").exists())
                self.assertFalse((root / directory / "../escape").exists())

    def test_all_catalogued_linux_bash_names_are_reachable_from_bin_and_sbin(self):
        # Exercise every valid Linux/Bash command mapped from the checked-in
        # SS64 catalog, not just a small hand-picked sample.
        repo_root = Path(__file__).resolve().parents[2]
        catalog_path = repo_root / "system/commands/ss64-command-catalog.json"
        if not catalog_path.is_file() or catalog_path.stat().st_size == 0:
            self.skipTest("SS64 catalog is a generated build artifact and is not populated in this checkout")
        import json
        import re
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        names = []
        for platform in catalog.get("platforms", {}).values():
            names.extend(row.get("name", "") for row in platform.get("commands", [])
                         if row.get("platform") == "linux_bash")
        names = sorted({name for name in names
                        if isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_.+-]+", name)})
        self.assertTrue(names, "SS64 catalog yielded no valid Linux/Bash command names")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "usr/bin").mkdir(parents=True)
            for name in names:
                (root / "usr/bin" / name).write_text("dispatcher", encoding="utf-8")
            counts = MODULE.install_command_path_aliases(root, names)
            self.assertEqual(counts, {"bin": len(names), "sbin": len(names)})
            for name in names:
                for directory in ("bin", "sbin"):
                    path = root / directory / name
                    self.assertTrue(path.exists() or path.is_symlink(), f"{directory}/{name}")
                    self.assertEqual(path.resolve(), (root / "usr/bin" / name).resolve(),
                                     f"incorrect {directory}/{name} target")

    def test_validator_rejects_missing_or_dangling_command_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bin").mkdir()
            (root / "sbin").mkdir()
            (root / "bin/missing").symlink_to("../usr/bin/missing")
            with self.assertRaisesRegex(RuntimeError, "SS64 command paths missing or dangling"):
                MODULE.validate_command_path_aliases(root, ["missing"])

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
