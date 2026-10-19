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

    def test_production_native_acceptance_gates_are_explicit_and_fail_closed(self):
        contract = json.loads((ROOT / "desktop/desktop-feature-contract.json").read_text())
        gates = contract["native_acceptance_gates"]
        self.assertEqual(len({gate["id"] for gate in gates}), len(gates))
        self.assertEqual({gate["id"] for gate in gates}, {
            "compositor", "display-input", "session-manager", "filesystem-clipboard",
            "device-services", "security-packages", "accessibility", "iso-desktop",
            "six-case", "end-to-end"
        })
        for gate in gates:
            self.assertTrue(gate["evidence_required"], gate["id"])
            self.assertNotEqual(gate["status"], "passed", gate["id"])
        self.assertEqual(contract["release_policy"]["status"], "blocked_until_all_required_gates_pass")
        self.assertTrue(any("weakened verifiers" in rule for rule in contract["release_policy"]["rules"]))

    def test_native_shell_tracks_child_process_lifecycle(self):
        source = (ROOT / "desktop/native/chimera-desktop-shell.cpp").read_text()
        self.assertIn("G_SPAWN_DO_NOT_REAP_CHILD", source)
        self.assertIn("g_child_watch_add(child_pid, child_exited", source)
        self.assertIn("g_spawn_close_pid(pid)", source)
        self.assertIn("Active child processes:", source)
        self.assertIn("not a compositor", source)

    def test_application_ecosystem_catalog_and_preview_apps(self):
        catalog = json.loads((ROOT / "desktop/application-ecosystem.json").read_text())
        self.assertEqual(catalog["schema"], "CHM-DESKTOP-APPLICATION-ECOSYSTEM-1")
        self.assertEqual({app["id"] for app in catalog["built_in_preview_apps"]}, {
            "paint", "media-player", "image-viewer", "games", "text-editor", "calculator"
        })
        self.assertIn("Windows", catalog["host_platform_reference"])
        self.assertIn("Linux", catalog["host_platform_reference"])
        self.assertIn("macOS", catalog["host_platform_reference"])
        allowed_states = set(catalog["integration_policy"]["app_states"])
        ids = [app["id"] for category in catalog["categories"] for app in category["applications"]]
        self.assertEqual(len(ids), len(set(ids)), "catalog app IDs must be unique")
        for category in catalog["categories"]:
            self.assertTrue(category["applications"], category["id"])
            for app in category["applications"]:
                self.assertIn(app["state"], allowed_states, app["id"])
                self.assertTrue(app["upstream"].startswith("https://"), app["id"])
                self.assertTrue(app["platforms"], app["id"])
        shell = (ROOT / "desktop/shared/desktop-parity.js").read_text()
        for app_id in ("paint", "media-player", "image-viewer", "games", "text-editor", "calculator", "app-catalog"):
            self.assertIn("id:'" + app_id + "'", shell)
        self.assertIn("function initPreviewApp", shell)
        self.assertIn("nativeSessionAdapter:false", shell)
        self.assertIn("Catalog entries describe integration candidates", shell)

    def test_shared_shell_javascript_syntax(self):
        try:
            subprocess.run(["node", "--check", str(ROOT / "desktop/shared/desktop-parity.js")],
                           check=True, capture_output=True, text=True)
        except FileNotFoundError:
            self.skipTest("Node.js is not installed; CI uses a runner-provided Node.js")

if __name__ == "__main__":
    unittest.main()
