"""Regression checks for the desktop locale, input and VoiceConnect ISO slice."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
IS_CHIMERA = (ROOT / "web" / "language-runtime.js").is_file()
JS = ROOT / ("web/language-runtime.js" if IS_CHIMERA else "desktop/shared/language-runtime.js")
KIOSK = ROOT / "live-image/lib/aurora-kiosk.py"
BUILDER = ROOT / "live-image/build.sh"
DESKTOP = ROOT / ("web/aurora_3d_desktop.html" if IS_CHIMERA else "desktop/aurora-wayland-glass/index.html")
INIT = ROOT / ("desktop/aurora/assets/Init.mp4" if IS_CHIMERA else "vendor/chimera-ii-os/source/desktop/aurora/assets/Init.mp4")
VOICECONNECT_COMMIT = "c3f0df816099b042486f5c5ec4405e2690690dc8"


class DesktopLanguageVoiceConnectTests(unittest.TestCase):
    def read(self, path):
        data = path.read_bytes()
        self.assertNotIn(b"\r\n", data, f"CRLF line ending found in {path.relative_to(ROOT)}")
        return data.decode("utf-8")

    def test_desktop_loads_shared_locale_runtime(self):
        html = self.read(DESKTOP)
        self.assertIn("language-runtime.js", html)
        source = self.read(JS)
        for token in ("Intl.getCanonicalLocales", "document.documentElement.dir", "SpeechSynthesisUtterance",
                      "SpeechRecognition", "aurora-locale-change", "aurora-input-language-change"):
            self.assertIn(token, source)

    def test_rtl_and_bcp47_locale_controls_exist(self):
        source = self.read(JS)
        for token in ('"ar"', '"fa"', '"he"', '"ur"', '"yi"', "supportedLocales", "BCP-47", "auroraDisplaySelect"):
            self.assertIn(token, source)
        self.assertIn('document.documentElement.dir = rtl.has(base) ? "rtl" : "ltr"', source)

    def test_native_input_bridge_is_allowlisted(self):
        kiosk = self.read(KIOSK)
        self.assertIn("setxkbmap", kiosk)
        self.assertIn("XKB_LAYOUTS", kiosk)
        self.assertTrue('payload.get("type") == "set-input-layout"' in kiosk or
                        'payload.get("type")=="set-input-layout"' in kiosk)
        self.assertNotIn("shell=True", kiosk)

    def test_voiceconnect_is_pinned_and_loopback_only(self):
        builder = self.read(BUILDER)
        kiosk = self.read(KIOSK)
        source = self.read(JS)
        self.assertIn(VOICECONNECT_COMMIT, builder)
        self.assertIn("npm ci --omit=dev --ignore-scripts", builder)
        self.assertIn("Node.js >=24", builder)
        self.assertTrue('"HOST": "127.0.0.1"' in kiosk or '"HOST":"127.0.0.1"' in kiosk)
        self.assertIn("127.0.0.1:8787", kiosk)
        self.assertIn('app:"voiceconnect"', source)
        self.assertIn("turn_credentials_embedded", builder)

    def test_reference_design_and_user_shortcuts_are_staged(self):
        design = ROOT / ("desktop/desktop-ecosystem-design.json" if IS_CHIMERA else "desktop/ecosystem-design.json")
        shortcut = ROOT / "desktop/shared/desktop-shortcuts.js"
        spec = json.loads(self.read(design))
        self.assertEqual({x["id"] for x in spec["desktops"]}, {"chimera", "octavian", "aurora", "koronos", "nova", "mobile"})
        self.assertTrue(spec["interaction"]["desktopShortcuts"]["create"])
        js = self.read(shortcut)
        for token in ("application", "document", "contextmenu", "localStorage", "noopener"):
            self.assertIn(token, js)

    def test_suno_collection_has_all_unique_user_links_and_language_groups(self):
        music = ROOT / ("desktop/aurora/media/suno-library.json" if IS_CHIMERA else "apps/suno-library.json")
        catalog = json.loads(self.read(music))
        urls = [track["url"] for track in catalog["tracks"]]
        self.assertEqual(len(urls), 57)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(catalog["count"], 57)
        self.assertIn("Japanese", {group["language"] for group in catalog["groups"]})
        self.assertIn("Arabic", {group["language"] for group in catalog["groups"]})
        self.assertTrue(all(url.startswith("https://suno.com/") for url in urls))

    def test_media_deck_exposes_suno_library_and_open_source_media_catalog(self):
        deck = ROOT / ("appcenter/media-deck.html" if IS_CHIMERA else "apps/media-deck.html")
        catalog = ROOT / ("desktop/aurora/media/open-source-media-apps.json" if IS_CHIMERA else "apps/open-source-media-apps.json")
        self.assertIn("suno-library.js", self.read(deck))
        self.assertIn("id=\"suno-tracks\"", self.read(deck))
        media = json.loads(self.read(catalog))
        self.assertTrue({"vlc", "mpv", "audacious", "obs-studio", "audacity", "ardour", "kdenlive", "ffmpeg"}.issubset({x["id"] for x in media["applications"]}))

    def test_real_init_video_is_available(self):
        self.assertTrue(INIT.is_file(), f"Missing Init.mp4 at {INIT}")
        self.assertGreater(INIT.stat().st_size, 0)
        builder = self.read(BUILDER)
        self.assertIn('INIT_VIDEO_SOURCE="$NATIVE_SOURCE/desktop/aurora/assets/Init.mp4"', builder)
        self.assertIn("Init.mp4", builder)


if __name__ == "__main__":
    unittest.main()
