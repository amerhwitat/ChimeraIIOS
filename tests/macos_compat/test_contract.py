#!/usr/bin/env python3
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / "tools/macos-compat/check-sdk.sh"
BUILD = ROOT / "tools/macos-compat/build-app.sh"
RUN = ROOT / "tools/macos-compat/run-app.sh"
DOC = ROOT / "docs/MACOS_COMPATIBILITY.md"

class MacOSCompatibilityContract(unittest.TestCase):
    def test_scripts_exist_and_document_limits(self):
        for p in (CHECK, BUILD, RUN, DOC):
            self.assertTrue(p.is_file(), str(p))
        text = DOC.read_text()
        self.assertIn("NOT IMPLEMENTED", text)
        self.assertIn("Do not promote an app", text)

    def test_non_apple_host_refuses_apple_sdk_profile(self):
        # This contract invokes a POSIX shell and is exercised on Linux CI.
        # Native macOS behavior belongs on a licensed Apple-hosted runner.
        if sys.platform != "linux":
            self.skipTest("Linux-only contract; macOS and Windows use dedicated validation")
        p = subprocess.run(["bash", str(CHECK), "apple-sdk"], text=True, capture_output=True)
        output = p.stdout + p.stderr
        self.assertEqual(p.returncode, 2, output)
        self.assertIn("Apple-branded macOS", output)

    def test_unknown_build_profile_fails_closed(self):
        p = subprocess.run(["bash", str(BUILD), "unknown", "missing.c", "/tmp/out"], text=True, capture_output=True)
        output = p.stdout + p.stderr
        self.assertNotEqual(p.returncode, 0, output)
        self.assertIn("unknown profile", output)

    def test_launcher_marks_portable_compat_mode(self):
        # Script contract test: assert explicit portable routing, not fake Mach-O support.
        text = RUN.read_text()
        self.assertIn("CHIMERA_MACOS_COMPAT=1", text)
        self.assertIn("UNSUPPORTED", text)
        self.assertIn("Darwin ABI/Frameworks runtime", text)

if __name__ == "__main__":
    unittest.main()
