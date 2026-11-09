#!/usr/bin/env python3
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPPER = ROOT / "tools/storage/chimera-wsl-drive-map.sh"
PROVISION = ROOT / "tools/provision-aurora-rootfs.sh"
STAGER = ROOT / "tools/stage-chimera-runtime.sh"
BUILD = ROOT / "build-chimera-iso.sh"


class WSLDriveMapTests(unittest.TestCase):
    def test_drvfs_drives_are_exposed_as_case_insensitive_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = pathlib.Path(temp)
            mnt = temp / "mnt"
            c_drive, d_drive = mnt / "c", mnt / "d"
            c_drive.mkdir(parents=True)
            d_drive.mkdir()
            fake_bin = temp / "bin"
            fake_bin.mkdir()
            findmnt = fake_bin / "findmnt"
            findmnt.write_text(r"""#!/bin/sh
case " $* " in
  *" -o SOURCE,TARGET,FSTYPE,OPTIONS "*) printf 'C:\\ %s 9p rw,aname=drvfs\nD:\\ %s 9p rw,aname=drvfs\n' "$FAKE_C" "$FAKE_D" ;;
  *) exit 1 ;;
esac
""")
            findmnt.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "WSL_INTEROP": "test",
                "CHIMERA_WSL_MNT_ROOT": str(mnt),
                "CHIMERA_WSL_DRIVE_ROOT": str(mnt / "drive"),
                "FAKE_C": str(c_drive),
                "FAKE_D": str(d_drive),
                "PATH": str(fake_bin) + os.pathsep + env["PATH"],
            })
            subprocess.run(["bash", str(MAPPER)], env=env, check=True, text=True, capture_output=True)
            for alias, target in (("c", c_drive), ("C", c_drive), ("d", d_drive), ("D", d_drive)):
                link = mnt / "drive" / alias
                self.assertTrue(link.is_symlink(), str(link))
                self.assertEqual(link.resolve(), target.resolve())

    def test_main_iso_builder_refreshes_wsl_drive_aliases(self):
        source = BUILD.read_text()
        self.assertIn('bash "$SCRIPT_DIR/tools/storage/chimera-wsl-drive-map.sh"', source)

    def test_aurora_dns_and_package_names_are_valid(self):
        source = PROVISION.read_text()
        self.assertIn(r"127\.", source)
        self.assertNotIn(r"127\\.", source)
        self.assertIn("swaybg swayidle mako wl-clipboard", source)
        self.assertNotIn("mako-notifier", source)
        self.assertIn("trap restore_resolver EXIT", source)
        self.assertIn("using cached package indexes and archive files only", source)
        self.assertIn("--no-download", source)
        self.assertIn("no usable cached package index exists", source)

    def test_staging_reports_provision_log_on_failure(self):
        source = STAGER.read_text()
        self.assertIn("Diagnostics: $AURORA_PROVISION_LOG", source)
        self.assertIn('tail -n 40 "$AURORA_PROVISION_LOG"', source)


if __name__ == "__main__":
    unittest.main()
