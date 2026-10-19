import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class DesktopParityContractTests(unittest.TestCase):
    def test_contract_declares_preview_and_native_gaps(self):
        contract = json.loads((ROOT / "desktop/desktop-feature-contract.json").read_text())
        self.assertEqual(contract["schema"], "CHM-DESKTOP-FEATURE-CONTRACT-1")
        self.assertEqual(contract["status"], "prototype-with-native-adapters-pending")
        self.assertIn("window open, focus, minimize, maximize, close and drag", contract["preview_features"])
        self.assertIn("real process launch and process supervision", contract["native_adapter_required"])
        self.assertIn("A browser preview or feature inventory must never be reported as a native desktop implementation.", contract["acceptance"]["policy"])

    def test_both_desktops_load_shared_shell(self):
        for rel in ("desktop/aurora-wayland-glass/index.html", "desktop/marine/index.html"):
            page = (ROOT / rel).read_text()
            self.assertIn('<script src="../shared/desktop-parity.js" defer></script>', page, rel)
            self.assertIn("Preview only", page, rel)

    def test_iso_staging_copies_desktop_tree(self):
        candidates = [
            ROOT / "iso/chimera-live-iso.sh",
            ROOT / "tools/build-full-iso.sh",
            ROOT / "vendor/chimera-ii-os/source/iso/chimera-live-iso.sh",
            ROOT / "vendor/chimera-ii-os/source/tools/build-full-iso.sh",
        ]
        scripts = [p.read_text() for p in candidates if p.is_file()]
        self.assertTrue(any('cp -a "$ROOT/desktop" "$STAGE/system/desktop"' in s for s in scripts),
                        "ISO builder must stage the full desktop tree, including shared shell assets")

    def test_shared_shell_exposes_truthful_capability_flag(self):
        script = (ROOT / "desktop/shared/desktop-parity.js").read_text()
        self.assertIn("nativeSessionAdapter:false", script)
        for feature in ("launcher-search", "window-management", "virtual-workspaces", "quick-settings", "accessibility-preferences"):
            self.assertIn(feature, script)

    def test_native_gtk_shell_has_search_and_navigation(self):
        source = (ROOT / "desktop/native/chimera-desktop-shell.cpp").read_text()
        self.assertIn("gtk_search_entry_new()", source)
        self.assertIn("filter_app_cards", source)
        self.assertIn("G_CALLBACK(nav_clicked)", source)
        self.assertIn("g_strstr_len", source)

    def test_shared_shell_javascript_syntax(self):
        try:
            subprocess.run(["node", "--check", str(ROOT / "desktop/shared/desktop-parity.js")],
                           check=True, capture_output=True, text=True)
        except FileNotFoundError:
            self.skipTest("Node.js is not installed; CI uses a runner-provided Node.js")

if __name__ == "__main__":
    unittest.main()
