import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("crawl_ss64.py")
SPEC = importlib.util.spec_from_file_location("crawl_ss64", MODULE_PATH)
crawl_ss64 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(crawl_ss64)


class MergedUsrCommandAliasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rootfs = self.root / "rootfs"
        self.repo = self.root / "repo"
        (self.repo / "system/commands").mkdir(parents=True)
        (self.rootfs / "usr/bin").mkdir(parents=True)
        (self.rootfs / "usr/sbin").mkdir(parents=True)
        (self.rootfs / "bin").symlink_to("usr/bin")
        (self.rootfs / "sbin").symlink_to("usr/sbin")
        dispatcher = self.rootfs / "usr/bin/chimera-compat"
        dispatcher.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        dispatcher.chmod(0o755)

    def test_repairs_legacy_self_links_in_merged_usr(self):
        # Reproduce the broken links left by the old /bin -> /usr/bin alias pass.
        for name in ("traceroute", "unrar"):
            (self.rootfs / "usr/bin" / name).symlink_to(name)

        catalog = {
            "platforms": {
                "linux_bash": {
                    "commands": [
                        {"name": "traceroute", "platform": "linux_bash", "source": "test"},
                        {"name": "unrar", "platform": "linux_bash", "source": "test"},
                    ]
                }
            }
        }
        manifest = crawl_ss64.reconcile(catalog, self.rootfs, self.repo)

        for name in ("traceroute", "unrar"):
            with self.subTest(name=name):
                self.assertTrue((self.rootfs / "usr/bin" / name).exists())
                self.assertTrue(os.access(self.rootfs / "usr/bin" / name, os.X_OK))
                self.assertTrue((self.rootfs / "bin" / name).exists())
                self.assertTrue((self.rootfs / "sbin" / name).exists())
                self.assertEqual(os.readlink(self.rootfs / "usr/bin" / name), "chimera-compat")
        self.assertEqual(manifest["path_aliases"]["/bin"], 2)
        self.assertEqual(manifest["path_aliases"]["/sbin"], 2)

    def test_preserves_existing_executable_and_does_not_self_link_bin(self):
        existing = self.rootfs / "usr/bin/realcmd"
        existing.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        existing.chmod(0o755)
        counts = crawl_ss64.install_command_path_aliases(self.rootfs, ["realcmd"])
        self.assertEqual(counts["bin"], 0)
        self.assertTrue(existing.is_file())
        self.assertFalse(existing.is_symlink())


if __name__ == "__main__":
    unittest.main()
