#!/usr/bin/env python3
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "desktop/aurora/aurora-init-splash.sh"
OSD = ROOT / "desktop/aurora/aurora-progress-osd.lua"
CMAKE = ROOT / "CMakeLists.txt"
SESSION = ROOT / "platform/systemd/aurora-session@.service"


class InitVideoProgressTests(unittest.TestCase):
    def test_media_is_hardcoded_into_system_install_paths(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        self.assertIn("desktop/aurora/assets/library/Init.mp4 DESTINATION boot/chimera", cmake)
        self.assertIn("desktop/aurora/aurora-init-splash.sh DESTINATION bin RENAME aurora-init-splash", cmake)
        self.assertIn("aurora-progress-osd.lua DESTINATION share/chimera/aurora", cmake)

    def test_splash_uses_live_progress_not_elapsed_time_as_progress(self):
        script = SCRIPT.read_text(encoding="utf-8")
        osd = OSD.read_text(encoding="utf-8")
        self.assertIn("/boot/chimera/Init.mp4", script)
        self.assertIn("/usr/share/chimera/aurora/assets/library/Init.mp4", script)
        self.assertIn("/run/chimera/koronos-progress.state", script)
        self.assertIn("--script=", script)
        self.assertIn("percent=", script)
        self.assertIn("mp.add_periodic_timer(0.25, render)", osd)
        self.assertIn("percent", osd)
        self.assertNotIn("percent = percent +", osd)

    def test_aurora_session_starts_splash_without_blocking_session_start(self):
        unit = SESSION.read_text(encoding="utf-8")
        self.assertIn("ExecStartPost=-/usr/bin/aurora-init-splash --background", unit)
        self.assertIn("ExecStart=/usr/lib/chimera/aurora-session", unit)


if __name__ == "__main__":
    unittest.main()
