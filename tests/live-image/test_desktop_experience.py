import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class DesktopExperienceContract(unittest.TestCase):
    def test_interaction_runtime_and_shortcuts_are_present(self):
        source = (ROOT / "desktop/shared/desktop-experience.js").read_text()
        for token in ("contextmenu", "dblclick", "renameTimer", '"F2"', '"Enter"', "chm-properties", "Network Apps", "VoiceConnect"):
            self.assertIn(token, source)
        self.assertIn("network-applications.html", source)

    def test_network_catalogue_has_voiceconnect_and_core_tools(self):
        data = json.loads((ROOT / "desktop/shared/network-applications.json").read_text())
        apps = {item["id"]: item for item in data["applications"]}
        for app in ("voiceconnect", "firefox", "openssh", "wireguard", "syncthing", "wireshark", "nmap"):
            self.assertIn(app, apps)
        self.assertIn("Messaging & calls", apps["voiceconnect"]["category"])

    def test_sdk_builder_is_fail_closed_when_strict(self):
        source = (ROOT / "tools/build-repository-sdks.sh").read_text()
        for token in ("CHIMERA_SDK_BUILD_STRICT", "sdk-build-results.tsv", "cmake", "cargo", "go.mod", "pom.xml", "package.json"):
            self.assertIn(token, source)

if __name__ == "__main__":
    unittest.main()
