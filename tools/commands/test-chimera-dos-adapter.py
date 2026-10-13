#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("chimera-dos-adapter.py")
SPEC = importlib.util.spec_from_file_location("chimera_dos_adapter", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class DosAdapterTests(unittest.TestCase):
    def test_rejects_shell_metacharacters(self):
        for value in ('x&y', 'x|y', 'x>y', 'x"y', 'x\ny'):
            self.assertFalse(MODULE.safe_dos_arg(value), value)

    def test_accepts_normal_dos_arguments(self):
        for value in ('GAME.EXE', 'save1.dat', 'LEVEL-2', 'hello world'):
            self.assertTrue(MODULE.safe_dos_arg(value), value)

    def test_missing_command_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse((Path(td) / 'append.exe').exists())

if __name__ == "__main__":
    unittest.main()
