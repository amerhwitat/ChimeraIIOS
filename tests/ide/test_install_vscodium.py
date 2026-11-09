import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/ide/install-vscodium.py"
SPEC = importlib.util.spec_from_file_location("install_vscodium", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class VSCodiumInstallPlanTests(unittest.TestCase):
    def test_linux_uses_flathub_flatpak(self):
        self.assertEqual(MODULE.install_plan("Linux", lambda x: "/usr/bin/flatpak"),
                         ["flatpak","install","--user","--noninteractive","flathub","com.vscodium.codium"])
    def test_windows_uses_winget(self):
        self.assertIn("VSCodium.VSCodium", MODULE.install_plan("Windows", lambda x: "winget"))
    def test_macos_uses_homebrew(self):
        self.assertEqual(MODULE.install_plan("Darwin", lambda x: "brew"),
                         ["brew","install","--cask","vscodium"])
    def test_missing_manager_is_reported(self):
        with self.assertRaises(RuntimeError):
            MODULE.install_plan("Linux", lambda x: None)
    def test_unknown_os_is_not_guessed(self):
        with self.assertRaises(RuntimeError):
            MODULE.install_plan("FreeBSD", lambda x: None)

if __name__ == "__main__":
    unittest.main()
