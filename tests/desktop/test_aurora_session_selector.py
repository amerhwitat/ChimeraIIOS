import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class AuroraSessionSelectorTests(unittest.TestCase):
    def test_selector_is_installed_by_cmake(self):
        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("desktop/aurora/aurora-session-select.sh", cmake)

    def test_selector_is_staged_into_live_runtime(self):
        stage = (ROOT / "tools/stage-chimera-runtime.sh").read_text()
        self.assertIn("aurora-session-select.sh", stage)

    def test_session_entry_invokes_selector_before_compositor(self):
        entry = (ROOT / "desktop/aurora/aurora-session.sh").read_text()
        self.assertLess(entry.index("chimera_select_desktop_profile"), entry.index('exec "$ROOT/aurora/aurora-start.sh"'))
        self.assertIn('SELECTOR="$SCRIPT_DIR/aurora-session-select.sh"', entry)

    def test_only_installed_external_desktops_are_offered(self):
        selector = (ROOT / "desktop/aurora/aurora-session-select.sh").read_text()
        for command, profile in (("marine-session", "marine"), ("gnome-session", "gnome"),
                                 ("startplasma-wayland", "plasma"), ("startxfce4", "xfce"),
                                 ("cinnamon-session", "cinnamon")):
            self.assertIn(f"command -v {command}", selector)
            self.assertIn(profile, selector)

    def test_labwc_fast_workspace_shortcuts(self):
        config = (ROOT / "desktop/aurora/labwc/rc.xml").read_text()
        for key in ("W-1", "W-2", "W-3", "W-4", "W-S-1", "W-S-2", "W-S-3", "W-S-4", "W-Tab"):
            self.assertIn(f'key="{key}"', config)

    def test_selector_shell_syntax(self):
        subprocess.run(["bash", "-n", str(ROOT / "desktop/aurora/aurora-session-select.sh")], check=True)
        subprocess.run(["bash", "-n", str(ROOT / "desktop/aurora/aurora-session.sh")], check=True)

if __name__ == "__main__":
    unittest.main()
