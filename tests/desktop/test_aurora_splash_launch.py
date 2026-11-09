#!/usr/bin/env python3
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "desktop/aurora/aurora-desktop-init.sh").read_text()


class AuroraSplashLaunchTests(unittest.TestCase):
    def test_splash_launch_is_not_gated_on_missing_primary_asset(self):
        self.assertIn('if [[ ! -s "$CHIMERA_INIT_VIDEO" ]]; then', SOURCE)
        self.assertIn('CHIMERA_INIT_VIDEO="$AURORA/assets/init.mp4"', SOURCE)
        self.assertIn('if [[ -s "$CHIMERA_INIT_VIDEO" ]]; then', SOURCE)
        self.assertIn('bash "$AURORA/aurora-init-splash.sh"', SOURCE)
        self.assertNotIn('[[ -s "$CHIMERA_INIT_VIDEO" ]] || CHIMERA_INIT_VIDEO=', SOURCE)

    def test_missing_optional_video_does_not_abort_session(self):
        self.assertIn('log "startup video unavailable; continuing without splash"', SOURCE)


if __name__ == "__main__":
    unittest.main()
