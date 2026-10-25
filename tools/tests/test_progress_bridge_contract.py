#!/usr/bin/env python3
"""Contract tests for real event-driven Init.mp4/Aurora progress state."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProgressBridgeContract(unittest.TestCase):
    def test_writer_and_aurora_reader_share_the_same_state_path(self):
        writer = (ROOT / "system/boot/koronos-progress.sh").read_text()
        ui = (ROOT / "desktop/aurora/aurora-progress.sh").read_text()
        self.assertIn('STATE_FILE="$STATE_DIR/koronos-progress.state"', writer)
        self.assertIn('STATE_FILE="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}"', ui)
        self.assertIn('mv -f "$tmp" "$STATE_FILE"', writer)
        self.assertIn("read_state", ui)

    def test_video_manifest_points_at_the_same_runtime_state(self):
        builder = (ROOT / "build-chimera-iso.sh").read_text()
        self.assertIn('"progress_state": "/run/chimera/koronos-progress.state"', builder)
        self.assertIn('"progress_ui": "/usr/share/chimera/aurora/aurora-progress.sh"', builder)

    def test_kernel_progress_events_are_emitted_at_real_init_milestones(self):
        kernel = (ROOT / "kernel/core/koronos.cpp").read_text()
        self.assertIn("CHIMERA_PROGRESS_EVENT percent=", kernel)
        self.assertIn('console_progress(25, "Architecture discovery and address-space safety checks complete")', kernel)
        self.assertIn('console_progress(75, "Process admission and module registries initialized")', kernel)
        self.assertIn('console_progress(100, "Kernel initialization complete; scheduler loop entered (not desktop readiness)")', kernel)

    def test_desktop_progress_requires_real_wayland_and_compositor_health(self):
        desktop = (ROOT / "desktop/aurora/aurora-desktop-init.sh").read_text()
        self.assertIn("wayland_socket_ready", desktop)
        self.assertIn("compositor_process_alive", desktop)
        self.assertIn('progress_set 100 aurora-session "Aurora desktop session initialized;', desktop)
        self.assertIn("refusing to report desktop readiness", desktop)
        self.assertIn('bash "$AURORA/aurora-init-splash.sh"', desktop)

    def test_splash_reads_percent_field_not_final_timestamp_line(self):
        splash = (ROOT / "desktop/aurora/aurora-init-splash.sh").read_text()
        self.assertIn('awk -F= \'$1=="percent" {print $2; exit}\'', splash)
        self.assertIn("tail -n 1", splash)

    def test_ui_reads_real_state_instead_of_advancing_a_completion_timer(self):
        ui = (ROOT / "desktop/aurora/aurora-progress.sh").read_text()
        self.assertIn('mapfile -t v < <(read_state', ui)
        self.assertNotIn("percent=$((percent +", ui)
        self.assertNotIn("pct=$((pct +", ui)


if __name__ == "__main__":
    unittest.main(verbosity=2)
