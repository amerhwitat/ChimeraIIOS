#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("chimera-wsl-drive-map.py")
SPEC = importlib.util.spec_from_file_location("chimera_wsl_drive_map", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WslDriveMapTests(unittest.TestCase):
    def test_maps_existing_drive_mounts_without_copying_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "mnt"
            (root / "c" / "Users").mkdir(parents=True)
            (root / "d").mkdir()
            mapped = MODULE.map_drives(root)
            self.assertEqual(mapped, ["c", "d"])
            self.assertTrue((root / "drive" / "c").is_symlink())
            self.assertTrue((root / "drive" / "C").is_symlink())
            self.assertEqual((root / "drive" / "c" / "Users").resolve(),
                             (root / "c" / "Users").resolve())

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "mnt"
            (root / "c").mkdir(parents=True)
            self.assertEqual(MODULE.map_drives(root), ["c"])
            self.assertEqual(MODULE.map_drives(root), ["c"])

    def test_refuses_to_replace_existing_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "mnt"
            (root / "c").mkdir(parents=True)
            (root / "drive" / "c").mkdir(parents=True)
            with self.assertRaises(RuntimeError):
                MODULE.map_drives(root)


if __name__ == "__main__":
    unittest.main()
