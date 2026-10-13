#!/usr/bin/env python3
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("chimera-dos-adapter.py")
SPEC = importlib.util.spec_from_file_location("chimera_dos_adapter", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class DosAdapterTests(unittest.TestCase):
    def test_rejects_shell_metacharacters(self):
        for value in ('x&y', 'x|y', 'x>y', 'x"y', 'x%PATH%', 'x!y', 'x\ny'):
            self.assertFalse(MODULE.safe_dos_arg(value), value)

    def test_accepts_normal_dos_arguments(self):
        for value in ('GAME.EXE', 'save1.dat', 'LEVEL-2', 'hello world'):
            self.assertTrue(MODULE.safe_dos_arg(value), value)

    def test_missing_command_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"CHIMERA_DOS_BIN": td}), patch.object(MODULE, "provider", return_value="/fake/dosbox"):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                rc = MODULE.main(["--command", "append"])
            self.assertEqual(rc, 127)
            self.assertIn("payload not installed", stderr.getvalue())

    def test_command_arguments_are_quoted_and_mount_is_read_only(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"CHIMERA_DOS_BIN": td}), patch.object(MODULE, "provider", return_value="/fake/dosbox"), patch.object(MODULE.subprocess, "run", return_value=type("R", (), {"returncode": 0})()) as run:
            (Path(td) / "append.exe").write_bytes(b"test payload")
            rc = MODULE.main(["--command", "append", "source path", "dest.dat"])
            self.assertEqual(rc, 0)
            args = run.call_args.args[0]
            self.assertEqual(args[0], "/fake/dosbox")
            self.assertIn(" -ro", args[2])
            self.assertIn('"append.exe" "source path" dest.dat', args)

    def test_dos_app_is_mounted_read_only_by_default(self):
        with tempfile.TemporaryDirectory() as td, patch.object(MODULE, "provider", return_value="/fake/dosbox"), patch.object(MODULE.subprocess, "run", return_value=type("R", (), {"returncode": 0})()) as run:
            program = Path(td) / "GAME.EXE"
            program.write_bytes(b"MZ")
            rc = MODULE.main(["--run", str(program), "level 2"])
            self.assertEqual(rc, 0)
            args = run.call_args.args[0]
            self.assertIn(" -ro", args[2])
            self.assertIn('"GAME.EXE" "level 2"', args)

if __name__ == "__main__":
    unittest.main()
