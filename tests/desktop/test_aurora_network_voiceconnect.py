import ast
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class AuroraNetworkAndVoiceConnectTests(unittest.TestCase):
    def test_network_panel_is_installed_and_staged(self):
        cmake = (ROOT / "CMakeLists.txt").read_text()
        stage = (ROOT / "tools/stage-chimera-runtime.sh").read_text()
        self.assertIn("network-applications.py", cmake)
        self.assertIn("network-applications.desktop", cmake)
        self.assertIn("network-applications.py", stage)
        self.assertIn("networking_panel.json", stage)

    def test_network_panel_uses_fixed_argv_without_shell(self):
        source = (ROOT / "desktop/aurora/network-applications.py").read_text()
        ast.parse(source)
        self.assertNotIn("shell=True", source)
        self.assertIn("authorized to assess", source)
        self.assertIn("if mode in (\"target\", \"target-terminal\") and not target", source)
        self.assertIn('["-sV", "-T3"]', source)

    def test_voiceconnect_launcher_is_optional_and_registered(self):
        launcher = ROOT / "desktop/aurora/voiceconnect-launcher.sh"
        subprocess.run(["bash", "-n", str(launcher)], check=True)
        registry = json.loads((ROOT / "desktop/aurora_app_registry.json").read_text())
        ids = {item["id"] for item in registry["apps"]}
        self.assertIn("voiceconnect", ids)
        self.assertIn("network-applications", ids)
        desktop = (ROOT / "desktop/aurora/voiceconnect.desktop").read_text()
        self.assertIn("voiceconnect-launcher.sh", desktop)

if __name__ == "__main__":
    unittest.main()
