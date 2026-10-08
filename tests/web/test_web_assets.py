import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class WebAssetsTest(unittest.TestCase):
    def test_required_assets_exist(self):
        for name in ("index.html", "chimera-hub.js", "chimera-hub.css",
                     "mame-web-runtime.js", "style.css", "data/chimera.json"):
            self.assertTrue((WEB / name).is_file(), name)

    def test_aurora_references_local_assets_and_hypervisor(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="style.css"', html)
        self.assertIn('src="chimera-hub.js"', html)
        self.assertIn('id="gamesGrid"', html)
        self.assertIn('id="hvProfile"', html)
        self.assertIn('id="hvGuests"', html)
        self.assertIn('data-view="hypervisor"', html)

    def test_hypervisor_ui_uses_local_bridge_and_explicit_nbit_status(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:8765", html)
        self.assertIn("/hypervisor/guests/start", html)
        self.assertIn("/hypervisor/guests/stop", html)
        self.assertIn("does not boot a guest OS", html)

    def test_manifest_schema_and_counts(self):
        data = json.loads((WEB / "data/chimera.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "chimera-ii-web-data")
        architecture = data["architecture"]
        self.assertEqual(architecture["depth"], len(architecture["layers"]))
        self.assertGreaterEqual(len(architecture["domains"]), 1)
        self.assertGreaterEqual(len(architecture["isa"]), 1)

    def test_javascript_has_fallback_and_manifest_loader(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn("const DATA_URL = 'data/chimera.json';", js)
        self.assertIn("fetch(DATA_URL", js)
        self.assertIn("render(fallback, 'fallback')", js)
        self.assertNotIn("innerHTML", js)


if __name__ == "__main__":
    unittest.main()
