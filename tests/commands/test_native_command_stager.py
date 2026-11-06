#!/usr/bin/env python3
"""Regression tests for non-destructive native command runtime staging."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
STAGER = ROOT / "tools/stage-native-command-runtime.sh"


class NativeCommandStagerTests(unittest.TestCase):
    def test_stages_native_commands_catalogues_and_dispatcher_without_replacing_coreutils(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "rootfs"
            system_bin = dest / "usr/bin"
            system_bin.mkdir(parents=True)
            sentinel = system_bin / "ls"
            sentinel.write_text("#!/bin/sh\necho system-ls-provider\n", encoding="utf-8")
            sentinel.chmod(0o755)

            env = dict(
                os.environ,
                CHIMERA_COMMAND_LINK_MODE="dynamic",
                CHIMERA_INSTALL_DISPATCHER="1",
                CHIMERA_STAGE_CATALOGS="1",
            )
            result = subprocess.run(
                ["bash", str(STAGER), str(ROOT), str(dest)],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            native_bin = dest / "usr/lib/chimera/native-bin"
            self.assertTrue((native_bin / "chimera-cmd").is_file())
            self.assertTrue((native_bin / "ls").is_symlink())
            self.assertTrue((native_bin / "echo").is_symlink())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "#!/bin/sh\necho system-ls-provider\n")
            self.assertFalse(sentinel.is_symlink())

            smoke = subprocess.run(
                [str(native_bin / "echo"), "native-stager-ok"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stderr)
            self.assertEqual(smoke.stdout.strip(), "native-stager-ok")

            commands = dest / "usr/share/chimera/commands"
            isa = dest / "usr/share/chimera/isa"
            self.assertTrue((commands / "chimera-run").is_file())
            self.assertTrue((commands / "os-command-runtime.json").is_file())
            self.assertTrue((commands / "catalogs/chimera-command-list.json").is_file())
            self.assertTrue((isa / "generated/universal-instruction-catalog.json").is_file())
            self.assertTrue((dest / "usr/bin/chimera").is_file())
            self.assertTrue((dest / "usr/bin/chimera-native").is_file())

            listing = subprocess.run(
                ["python3", str(commands / "chimera-run"), "--list"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(listing.returncode, 0, listing.stdout + listing.stderr)
            self.assertIn("chimera-native", listing.stdout)


if __name__ == "__main__":
    unittest.main()
