import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "installer" / "cross-distro-workflow.json"
HTML = ROOT / "installer" / "gui" / "aurora-installer.html"
JS = ROOT / "installer" / "gui" / "aurora-installer.js"
CSS = ROOT / "installer" / "gui" / "aurora-installer.css"


class CrossDistroInstallerWorkflowTests(unittest.TestCase):
    def test_cross_distro_wizard_contract_is_safety_first_and_shared(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            {x["project"] for x in data["design_influences"]},
            {"Red Hat Anaconda / CentOS", "Linux Mint / Ubuntu", "Debian Installer", "SUSE YaST"},
        )
        self.assertEqual(data["shared_frontend_contract"]["executor"], "Installer::build_plan + Installer::execute")
        self.assertTrue(data["storage_safety"]["dry_run_default"])
        self.assertFalse(data["storage_safety"]["erase_default"])
        self.assertEqual(data["storage_safety"]["unsupported_operation"], "fail_closed")
        self.assertTrue(data["acceptance"]["require_exact_iso_sha256"])

    def test_gui_has_guided_custom_storage_review_and_fail_closed_commit(self):
        html = HTML.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("Guided — propose layout", js)
        self.assertIn("Custom — expert layout", js)
        self.assertIn("Review & Commit", js)
        self.assertIn("INSTALLATION BLOCKED (status 78)", js)
        self.assertIn("No disk changes have been made", js)
        self.assertIn('aria-label="Installation steps"', html)
        self.assertIn("aurora-installer.css", html)
        self.assertIn(":focus-visible", css)

    def test_gui_does_not_claim_native_backend_or_fake_install_success(self):
        js = JS.read_text(encoding="utf-8")
        self.assertIn("Backend: unavailable", js)
        self.assertIn("Transaction: not started", js)
        self.assertIn("Disk writes: none", js)

    def test_installer_localization_picker_catalog_and_rtl_contract(self):
        html = HTML.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        catalog = (ROOT / "installer" / "gui" / "installer-i18n.js").read_text(encoding="utf-8")
        ui_contract = json.loads((ROOT / "installer" / "gui" / "aurora-installer-ui.json").read_text(encoding="utf-8"))
        self.assertEqual(ui_contract["localization"]["locale_standard"], "BCP-47")
        self.assertTrue(ui_contract["localization"]["rtl_layout"])
        self.assertIn('id="uiLanguage"', html)
        self.assertIn('src="installer-i18n.js"', html)
        self.assertIn("Intl.getCanonicalLocales", catalog)
        self.assertIn("const rtl=new Set", catalog)
        self.assertIn("'ar':", catalog)
        self.assertIn("'zh':", catalog)
        self.assertIn("'ja':", catalog)
        self.assertIn("setLocale", js)
        self.assertIn("document.documentElement.dir", js)
        self.assertIn("English fallback", js)


    def test_full_iso_workflow_fails_when_userspace_acceptance_is_false(self):
        workflow = (ROOT / ".github" / "workflows" / "chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn("name: Fail workflow when target userspace acceptance is missing", workflow)
        self.assertIn("if: steps.userspace_gate.outputs.accepted != 'true'", workflow)
        self.assertIn("steps.userspace_gate.outputs.accepted == 'true'", workflow)
        gate = workflow.index("name: Fail workflow when target userspace acceptance is missing")
        publish = workflow.index("name: Publish validated ISO candidate to GitHub Releases", gate)
        self.assertIn("exit 1", workflow[gate:publish])


if __name__ == "__main__":
    unittest.main()
