#!/usr/bin/env python3
"""Validate cross-OS app/settings/driver/CPU compatibility contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "config/platform/os-compatibility.json"
DRIVER = ROOT / "config/hardware/driver-assistant-policy.json"
SETTINGS = ROOT / "config/settings/control-panel-registry.json"

def load(path):
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SystemExit(f"invalid schema envelope: {path.relative_to(ROOT)}")
    return value

compat = load(COMPAT)
driver = load(DRIVER)
settings = load(SETTINGS)

allowed = set(compat["rules"]["status_values"])
assert compat["rules"]["default_status"] in allowed
os_entries = compat["operating_system_families"]
os_ids = [entry["id"] for entry in os_entries]
assert len(os_ids) == len(set(os_ids)), "duplicate OS family IDs"
for entry in os_entries:
    status = entry.get("status", entry.get("support_mode", "not_tested"))
    assert status in allowed, f"invalid compatibility status for {entry['id']}: {status}"
for required in ("chimera", "octavian", "linux", "windows", "macos"):
    assert required in os_ids, f"missing OS family: {required}"
for entry in compat["cpu_profiles"]:
    assert entry["status"] in allowed, f"invalid CPU status for {entry['id']}"

sections = settings["sections"]
section_ids = [section["id"] for section in sections]
assert len(section_ids) == len(set(section_ids)), "duplicate settings section IDs"
setting_ids = [setting for section in sections for setting in section["settings"]]
assert len(setting_ids) == len(set(setting_ids)), "duplicate setting IDs"
for required in ("devices", "compatibility", "applications", "security", "platform_specific"):
    assert required in section_ids, f"missing control-panel section: {required}"
assert settings["apply_contract"]["no_silent_fallback"] is True

for required in ("inventory", "catalog_match", "policy_check", "sandbox_probe", "acceptance", "audit"):
    assert any(step["name"] == required for step in driver["pipeline"]), f"missing driver pipeline step: {required}"
for forbidden in ("load_or_execute_model_generated_kernel_code", "bypass_signature_or_trust_policy"):
    assert forbidden in driver["model_role"]["forbidden"], f"missing safety guard: {forbidden}"
assert driver["learning_policy"]["offline_first"] is True
assert "bound_verified" in driver["driver_states"]

print(f"cross-OS contracts PASS: {len(os_entries)} OS families, "
      f"{len(compat['cpu_profiles'])} CPU profiles, {len(setting_ids)} settings, "
      f"{len(driver['pipeline'])} driver-assistant stages")
