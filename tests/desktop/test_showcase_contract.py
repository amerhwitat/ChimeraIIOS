import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOWCASE = ROOT / "desktop" / "showcase" / "index.html"
MATRIX = ROOT / "desktop" / "showcase" / "desktop-matrix.json"


class DesktopShowcaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = SHOWCASE.read_text(encoding="utf-8")
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_all_six_named_environments_are_present(self):
        expected = {
            "ChimeraIIOS Desktop", "OctavianOS Desktop", "Aurora Desktop",
            "Koronos Desktop", "Nova Desktop", "Mobile OS (Tablet/Phone)"
        }
        self.assertEqual(expected, {item["name"] for item in self.matrix["environments"]})
        for name in expected:
            self.assertIn(name, self.html)

    def test_shared_ui_contracts_exist(self):
        for capability in self.matrix["shared_preview_capabilities"]:
            self.assertTrue(capability, "empty capability")
        for token in ("data-menu", "data-app", "aria-live", "prefers-reduced-motion",
                      "Escape", "wallpaper", "Screen Savers"):
            self.assertIn(token.lower(), self.html.lower())

    def test_native_readiness_is_not_overclaimed(self):
        self.assertEqual("prototype-not-native-session", self.matrix["runtime_status"])
        self.assertIn("not evidence of native app execution", self.matrix["policy"])
        self.assertIn("Prototype UI only", self.html)

    def test_all_profiles_have_a_native_acceptance_state(self):
        for item in self.matrix["environments"]:
            self.assertTrue(item["ui"], item["id"])
            self.assertIn("native_session", item)
            self.assertNotEqual("production-ready", item["native_session"])


if __name__ == "__main__":
    unittest.main()
