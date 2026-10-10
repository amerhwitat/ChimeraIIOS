#!/usr/bin/env python3
"""Unit tests for the portable Chimera Hosted Edition bridge."""
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("chimera_hosted", ROOT / "tools/runtime/chimera-hosted.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class HostedRuntimeTests(unittest.TestCase):
    def test_host_info_reports_pointer_width_and_isa_fields(self):
        data = MOD.info()
        self.assertIn("host_isa", data)
        self.assertIn("pointer_bits", data)
        self.assertIn("runtime_kind", data)

    def test_32_bit_windows_profile_is_supported(self):
        with patch.object(MOD.sys, "maxsize", 2**31 - 1), patch.object(MOD, "host_family", return_value="windows"), patch.object(MOD, "host_isa", return_value="x86-32"):
            data = MOD.info()
        self.assertEqual(data["pointer_bits"], 32)
        self.assertEqual(data["host_word_bits"], 32)
        self.assertEqual(data["hosted_profile"], "32-bit-user-space")
        self.assertTrue(data["hosted_edition_supported"])

    def test_32_bit_macos_profile_is_not_claimed_supported(self):
        with patch.object(MOD.sys, "maxsize", 2**31 - 1), patch.object(MOD, "host_family", return_value="macos"), patch.object(MOD, "host_isa", return_value="x86-32"):
            data = MOD.info()
        self.assertFalse(data["hosted_edition_supported"])

    def test_windows_command_aliases(self):
        result = MOD.translate("ls", "windows")
        self.assertEqual(result["canonical"], "dir")
        self.assertTrue(result["alias_applied"])

    def test_posix_command_aliases(self):
        result = MOD.translate("type", "linux")
        self.assertEqual(result["canonical"], "cat")

    def test_unknown_compat_mode_falls_back_safely(self):
        result = MOD.translate("echo", "not-a-mode")
        self.assertEqual(result["mode"], "linux")
        self.assertEqual(result["canonical"], "echo")

    def test_file_copy_builtin(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp) / "source.txt"
            dst = pathlib.Path(tmp) / "dest.txt"
            src.write_text("Chimera", encoding="utf-8")
            self.assertEqual(MOD.builtin(["cp", str(src), str(dst)]), 0)
            self.assertEqual(dst.read_text(encoding="utf-8"), "Chimera")

    def test_remove_refuses_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(MOD.builtin(["rm", tmp]), 2)

    def test_isa_database_loader_is_fail_safe(self):
        data = MOD.load_isa_db()
        self.assertIsInstance(data.get("architectures"), list)

if __name__ == "__main__":
    unittest.main()
