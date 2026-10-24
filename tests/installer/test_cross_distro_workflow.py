import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "installer" / "cross-distro-workflow.json"
HTML = ROOT / "installer" / "gui" / "aurora-installer.html"
JS = ROOT / "installer" / "gui" / "aurora-installer.js"
CSS = ROOT / "installer" / "gui" / "aurora-installer.css"


def test_cross_distro_wizard_contract_is_safety_first_and_shared():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert {x["project"] for x in data["design_influences"]} == {
        "Red Hat Anaconda / CentOS", "Linux Mint / Ubuntu", "Debian Installer", "SUSE YaST"
    }
    assert data["shared_frontend_contract"]["executor"] == "Installer::build_plan + Installer::execute"
    assert data["storage_safety"]["dry_run_default"] is True
    assert data["storage_safety"]["erase_default"] is False
    assert data["storage_safety"]["unsupported_operation"] == "fail_closed"
    assert data["acceptance"]["require_exact_iso_sha256"] is True


def test_gui_has_guided_custom_storage_review_and_fail_closed_commit():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "Guided — propose layout" in js
    assert "Custom — expert layout" in js
    assert "Review & Commit" in js
    assert "INSTALLATION BLOCKED (status 78)" in js
    assert "No disk changes have been made" in js
    assert 'aria-label="Installation steps"' in html
    assert "aurora-installer.css" in html


def test_gui_progress_is_not_faked_and_no_backend_is_claimed():
    js = JS.read_text(encoding="utf-8")
    assert "Backend: unavailable" in js
    assert "Transaction: not started" in js
    assert "Disk writes: none" in js
