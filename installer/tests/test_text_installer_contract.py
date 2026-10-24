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

CORE = (ROOT / "src" / "installer_core.cpp").read_text(encoding="utf-8")
HEADER = (ROOT / "include" / "chimera" / "installer_core.hpp").read_text(encoding="utf-8")
POLICY = (ROOT / "config" / "installed-system-policy.json").read_text(encoding="utf-8")


def test_installer_collects_locale_timezone_keyboard_and_input_languages():
    assert 'plan.locale = ask_text' in CLI
    assert 'plan.timezone = ask_text' in CLI
    assert 'plan.keyboard_layout = ask_text' in CLI
    assert 'plan.input_languages = ask_text' in CLI
    for field in ("locale", "timezone", "keyboard_layout", "input_languages", "hardware_clock_utc", "enable_ntp"):
        assert field in HEADER


def test_gui_and_text_share_fail_closed_executor():
    assert 'INSTALLATION BLOCKED' in CORE
    assert 'return 78;' in CORE
    assert 'if(p.dry_run)' in CORE
    # The previous unsafe copy-and-success path must not remain in execute().
    execute = CORE[CORE.index("int Installer::execute("):]
    assert "copy_tree(p.source_root,p.target_root)" not in execute
    assert "return 78;" in execute


def test_linux_layout_and_ntfs_fat_safety_are_explicit():
    assert 'Linux filesystem layout' in CORE
    assert 'NTFS' in CORE and 'FAT16' in CORE and 'FAT32' in CORE
    assert '"fstab_source": "verified_partition_uuid_only"' in POLICY
    assert '"never_force_dirty_or_hibernated_volume": true' in POLICY
    assert '"missing_capability_policy": "fail_closed"' in POLICY
