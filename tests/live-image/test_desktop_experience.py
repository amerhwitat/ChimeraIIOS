import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class DesktopExperienceContract(unittest.TestCase):
    def test_interaction_runtime_and_shortcuts_are_present(self):
        source = (ROOT / "desktop/shared/desktop-experience.js").read_text()
        for token in ("contextmenu", "dblclick", "renameTimer", '"F2"', '"Enter"', "chm-properties", "body button,body .shortcut", "Network Apps", "VoiceConnect", "Linux Workspace", 'else if(k==="t")', 'else if(k==="f")'):
            self.assertIn(token, source)
        self.assertIn("network-applications.html", source)

    def test_network_catalogue_has_voiceconnect_and_core_tools(self):
        data = json.loads((ROOT / "desktop/shared/network-applications.json").read_text())
        apps = {item["id"]: item for item in data["applications"]}
        for app in ("voiceconnect", "firefox", "openssh", "wireguard", "syncthing", "wireshark", "nmap"):
            self.assertIn(app, apps)
        self.assertIn("Messaging & calls", apps["voiceconnect"]["category"])
        self.assertIn("feat/voiceconnect-p2p-camera", apps["voiceconnect"]["project"])
        panel = (ROOT / "desktop/shared/network-applications.html").read_text()
        self.assertIn("Copy launch command", panel)
        self.assertIn("Development branch", panel)
        self.assertTrue((ROOT / "desktop/plasma/index.html").is_file())
        self.assertTrue((ROOT / "desktop/shared/linux-workspace.desktop").is_file())
        launcher = (ROOT / "desktop/shared/voiceconnect-launcher.sh").read_text()
        self.assertIn("https://github.com/amerhwitat/test", launcher)
        desktop = (ROOT / "desktop/shared/voiceconnect-project.desktop").read_text()
        self.assertIn("Exec=/usr/local/bin/voiceconnect-launcher", desktop)

    def test_sdk_builder_is_fail_closed_when_strict(self):
        source = (ROOT / "tools/build-repository-sdks.sh").read_text()
        for token in ("CHIMERA_SDK_BUILD_STRICT", "sdk-build-results.tsv", "cmake", "cargo", "go.mod", "pom.xml", "package.json"):
            self.assertIn(token, source)

if __name__ == "__main__":
    unittest.main()
