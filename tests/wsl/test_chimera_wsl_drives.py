import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "wsl" / "chimera-wsl-drives.py"
SPEC = importlib.util.spec_from_file_location("chimera_wsl_drives", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WslDriveConfigurationTests(unittest.TestCase):
    def test_configure_sets_drvfs_root_and_preserves_other_sections(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / "wsl.conf"
            mount_root = root / "mnt" / "drive"
            config.write_text("[boot]\nsystemd=true\n", encoding="utf-8")
            with mock.patch.object(MODULE, "is_wsl", return_value=True), \
                 mock.patch.object(MODULE.os, "geteuid", return_value=0):
                MODULE.configure(config, mount_root)
            result = config.read_text(encoding="utf-8")
            self.assertIn("systemd = true", result)
            self.assertIn("root = " + str(mount_root), result)
            self.assertIn("options = metadata,umask=22,fmask=11", result)
            self.assertTrue(mount_root.is_dir())
            self.assertTrue(config.with_name("wsl.conf.chimera-backup").is_file())

    def test_configure_refuses_non_wsl_host(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(MODULE, "is_wsl", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "requires a WSL2"):
                    MODULE.configure(Path(td) / "wsl.conf", Path(td) / "drive")

    def test_status_refuses_non_wsl_host(self):
        with mock.patch.object(MODULE, "is_wsl", return_value=False):
            self.assertEqual(MODULE.status(Path("/mnt/drive")), 2)


if __name__ == "__main__":
    unittest.main()
