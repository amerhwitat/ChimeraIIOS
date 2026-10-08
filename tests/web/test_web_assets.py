import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class WebAssetsTest(unittest.TestCase):
    def test_required_assets_exist(self):
        for name in ("index.html", "app.js", "style.css", "data/chimera.json",
                     "chimera_code_ide.html", "chimera_code_ide.js",
                     "chimera_code_ide.css", "aurora-ide-catalog.json",
                     "system_control_center.html"):
            self.assertTrue((WEB / name).is_file(), name)

    def test_html_references_local_assets(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="style.css"', html)
        self.assertIn('src="app.js"', html)
        self.assertIn('id="cards"', html)
        self.assertIn('id="isa"', html)
        self.assertIn('id="kernel"', html)

    def test_native_ide_file_associations_and_toolchain_boundary(self):
        html = (WEB / "chimera_code_ide.html").read_text(encoding="utf-8")
        js = (WEB / "chimera_code_ide.js").read_text(encoding="utf-8")
        self.assertIn('id="openBtn"', html)
        self.assertIn('id="saveBtn"', html)
        self.assertIn("aurora-ide-catalog.json", js)
        self.assertIn("No working toolchain service is connected", js)
        catalog = json.loads((WEB / "aurora-ide-catalog.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in catalog["ides"]}
        self.assertTrue({"vscode", "vscodium", "qt-creator"}.issubset(ids))

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
