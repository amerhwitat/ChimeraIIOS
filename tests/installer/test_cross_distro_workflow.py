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


if __name__ == "__main__":
    unittest.main()
