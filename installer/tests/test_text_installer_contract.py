from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = (ROOT / "src" / "installer_cli.cpp").read_text(encoding="utf-8")


def test_text_frontend_uses_shared_installer_planner_and_executor():
    assert 'Installer installer;' in CLI
    assert 'installer.build_plan(plan)' in CLI
    assert 'installer.execute(plan, false)' in CLI


def test_text_frontend_never_claims_install_success_without_transaction_backend():
    assert 'INSTALLATION BLOCKED' in CLI
    assert 'return 78;' in CLI
    assert 'no success is claimed' in CLI
    assert 'Attempt an actual installation now?' in CLI


def test_text_frontend_is_keyboard_only_and_has_explicit_review():
    assert 'keyboard-only text mode' in CLI
    assert 'Review the shared installation plan?' in CLI
    assert 'Target root (mounted target only)' in CLI
