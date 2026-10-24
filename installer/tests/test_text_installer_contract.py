from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = (ROOT / "src" / "installer_cli.cpp").read_text(encoding="utf-8")


def test_text_frontend_uses_shared_installer_planner_and_executor():
    assert 'Installer installer;' in CLI
    assert 'installer.build_plan(plan)' in CLI
    assert 'installer.execute(plan, false)' in CLI


def test_text_frontend_never_claims_install_success_without_transaction_backend():
    assert 'INSTALLATION BLOCKED' in CORE
    assert 'return 78;' in CORE
    assert 'no success is claimed' in CLI
    assert 'Attempt an actual installation now?' in CLI
    assert 'return installer.execute(plan, true);' in CLI


def test_text_frontend_is_keyboard_only_and_has_explicit_review():
    assert 'keyboard-only text mode' in CLI
    assert 'Start the installer wizard?' in CLI
    assert 'Target root (mounted target only)' in CLI


CORE = (ROOT / "src" / "installer_core.cpp").read_text(encoding="utf-8")
HEADER = (ROOT / "include" / "chimera" / "installer_core.hpp").read_text(encoding="utf-8")
GUI = (ROOT / "src" / "installer_gui.cpp").read_text(encoding="utf-8")
CMAKE = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
FLOW = (ROOT / "cross-distro-workflow.json").read_text(encoding="utf-8")
POLICY = (ROOT / "config" / "installed-system-policy.json").read_text(encoding="utf-8")


def test_installer_collects_locale_timezone_keyboard_and_input_languages():
    assert 'plan.locale = ask_text' in CLI
    assert 'plan.timezone = ask_text' in CLI
    assert 'plan.keyboard_layout = ask_text' in CLI
    assert 'plan.input_languages = ask_text' in CLI
    assert 'plan.storage_mode = ask_text' in CLI
    assert 'plan.edition = ask_text' in CLI
    assert 'plan.desktop_profile = ask_text' in CLI
    for field in ("locale", "timezone", "keyboard_layout", "input_languages", "hardware_clock_utc", "enable_ntp"):
        assert field in HEADER


def test_gui_and_text_share_fail_closed_executor():
    assert 'INSTALLATION BLOCKED' in CORE
    assert 'return 78;' in CORE
    assert 'if(p.dry_run)' in CORE
    execute = CORE[CORE.index("int Installer::execute("):]
    assert "copy_tree(p.source_root,p.target_root)" not in execute
    assert "return 78;" in execute


def test_linux_layout_and_ntfs_fat_safety_are_explicit():
    assert 'Linux filesystem layout' in CORE
    assert 'NTFS' in CORE and 'FAT16' in CORE and 'FAT32' in CORE
    assert '"fstab_source": "verified_partition_uuid_only"' in POLICY
    assert '"never_force_dirty_or_hibernated_volume": true' in POLICY
    assert '"missing_capability_policy": "fail_closed"' in POLICY


TARGETS = (ROOT / "config" / "live-target-parity.json").read_text(encoding="utf-8")


def test_live_installer_and_recovery_target_require_same_boot_and_service_chain():
    for stage in ("spit-fire", "jasper-grub", "koronos-elf", "scheduler-runtime", "target-services"):
        assert stage in TARGETS
    for target in ('"live"', '"installer"', '"recovery"'):
        assert target in TARGETS
    assert '"same_iso_sha256_required_for_all_traces": true' in TARGETS
    assert '"simulated_smp_is_invalid": true' in TARGETS


def test_settings_summary_uses_real_line_breaks_not_literal_backslash_sequences():
    # Two backslashes followed by n in a C++ string print the characters \\n,
    # rather than the intended line break.
    assert '<< "\\\\nLocale:' not in CLI
    assert '<< "\\\\nTime zone:' not in CLI
    assert '<< "\\\\nKeyboard:' not in CLI

def test_text_frontend_collects_cross_distro_wizard_choices():
    for field in ("source_type", "network_mode", "hostname", "admin_username", "firewall_enabled", "secure_boot", "storage_mode", "edition", "desktop_profile", "preserve_existing_os", "encrypt_root"):
        assert field in HEADER
    for prompt in ("Source type", "Network mode", "Installed system hostname", "Administrator username", "Storage mode", "System role", "Desktop profile"):
        assert prompt in CLI
    assert "source_type" in CORE and "network_mode" in CORE


def test_gui_launcher_packages_accessible_wizard_and_remains_fail_closed():
    assert "aurora-installer.html" in GUI
    assert "xdg-open" in GUI
    assert "INSTALLER GUI UNAVAILABLE" in GUI
    assert "cross-distro-workflow.json DESTINATION share/chimera/installer" in CMAKE
    assert "install(DIRECTORY gui/" in CMAKE
    assert "PATTERN \"aurora-installer-ui.json\"" in CMAKE
    for distro in ("Red Hat Anaconda / CentOS", "Linux Mint / Ubuntu", "Debian Installer", "SUSE YaST"):
        assert distro in FLOW

def test_release_artifact_is_blocked_without_exact_iso_daps():
    release = (ROOT.parent / ".github" / "workflows" / "chimera-release.yml").read_text(encoding="utf-8")
    assert "production_acceptance_gate.py" in release
    assert "--evidence-dir production-evidence" in release
