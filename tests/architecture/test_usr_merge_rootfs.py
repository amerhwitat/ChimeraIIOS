#!/usr/bin/env python3
"""Regression tests for the staged rootfs usr-merge layout helper."""
import os
import pathlib
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
HELPER = REPO / "tools" / "prepare-usr-merge-rootfs.sh"


class UsrMergeRootfsTests(unittest.TestCase):
    def run_helper(self, root):
        env = os.environ.copy()
        env["CHIMERA_ROOTFS_DIR"] = str(root)
        return subprocess.run(
            ["bash", str(HELPER)], env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_migrates_legacy_commands_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "bin").mkdir()
            (root / "sbin").mkdir()
            (root / "bin" / "hello").write_text("#!/bin/sh\necho hello\n")
            (root / "sbin" / "daemon").write_text("daemon-binary-placeholder")
            first = self.run_helper(root)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((root / "usr/bin/hello").is_file())
            self.assertTrue((root / "usr/sbin/daemon").is_file())
            self.assertTrue((root / "bin").is_symlink())
            self.assertEqual(os.readlink(root / "bin"), "/usr/bin")
            self.assertTrue((root / "sbin").is_symlink())
            self.assertEqual(os.readlink(root / "sbin"), "/usr/sbin")
            second = self.run_helper(root)
            self.assertEqual(second.returncode, 0, second.stderr)

    def test_identical_collision_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "bin").mkdir()
            (root / "usr/bin").mkdir(parents=True)
            (root / "bin/tool").write_text("same")
            (root / "usr/bin/tool").write_text("same")
            result = self.run_helper(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "usr/bin/tool").read_text(), "same")

    def test_different_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "bin").mkdir()
            (root / "usr/bin").mkdir(parents=True)
            (root / "bin/tool").write_text("legacy")
            (root / "usr/bin/tool").write_text("canonical")
            result = self.run_helper(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite", result.stderr)
            self.assertEqual((root / "bin/tool").read_text(), "legacy")
            self.assertEqual((root / "usr/bin/tool").read_text(), "canonical")

    def test_rejects_wrong_existing_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "bin").symlink_to("usr/local/bin")
            result = self.run_helper(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
