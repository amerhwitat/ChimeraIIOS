import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

class DesktopGalleryArtworkTests(unittest.TestCase):
    def test_gallery_profiles_have_artwork_and_controls(self):
        page = (ROOT / "web/desktop-showcase/index.html").read_text(encoding="utf-8")
        for profile in ("aurora", "marine", "freexp", "freewin11"):
            self.assertIn(f'data-style="{profile}"', page)
            self.assertIn(f'data-select="{profile}"', page)
            artwork = ROOT / "web/desktop-showcase/artwork" / f"{profile}.svg"
            self.assertTrue(artwork.is_file(), str(artwork))
            ET.parse(artwork)

    def test_webgl_gallery_has_real_settings_dialog_and_no_fake_ready_claim(self):
        page = (ROOT / "web/aurora_webgl_desktops.html").read_text(encoding="utf-8")
        script = (ROOT / "web/aurora_webgl_desktops.js").read_text(encoding="utf-8")
        self.assertIn('id="settingsDialog"', page)
        self.assertIn('id="settingsApply"', page)
        self.assertIn("renderer.setPixelRatio", script)
        self.assertIn("backend required", script)
        self.assertNotIn("ready</b>", script)

    def test_service_catalog_and_registry_parse(self):
        catalog = json.loads((ROOT / "services/linux/service-catalog.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "services/service_registry.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in catalog["services"]}
        self.assertTrue({"wireplumber", "greetd", "seatd", "xdg-desktop-portal"} <= ids)
        registry_ids = {item["id"] for item in registry["services"]}
        self.assertTrue({"session-manager", "desktop-portals", "graphics-session"} <= registry_ids)

if __name__ == "__main__":
    unittest.main()
