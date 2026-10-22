#!/usr/bin/env python3
"""Validate cross-OS app/settings/driver/CPU compatibility contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "config/platform/os-compatibility.json"
DRIVER = ROOT / "config/hardware/driver-assistant-policy.json"
SETTINGS = ROOT / "config/settings/control-panel-registry.json"
CATALOG = ROOT / "docs/OPEN_SOURCE_USERSPACE_CATALOG.json"

def load(path):
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SystemExit(f"invalid schema envelope: {path.relative_to(ROOT)}")
    return value

compat = load(COMPAT)
driver = load(DRIVER)
settings = load(SETTINGS)
catalog = load(CATALOG)

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
assert driver["implementation_status"] == "policy_only_no_RNN_or_LLM_inference_backend_linked"
assert "bound_verified" in driver["driver_states"]

families = catalog["application_families"]
family_ids = [family["id"] for family in families]
assert len(family_ids) == len(set(family_ids)), "duplicate application family IDs"
target_matrix = catalog["target_os_matrix"]
target_ids = [target["id"] for target in target_matrix]
assert len(target_ids) == len(set(target_ids)), "duplicate app target IDs"
for required in ("chimera", "octavian", "linux", "windows", "macos"):
    assert required in target_ids, f"missing app target: {required}"
for target in target_matrix:
    assert target["status"] == "candidate_only" and target["provider_required"] is True, (
        f"target {target['id']} must remain gated on provider and evidence"
    )
for family in families:
    assert family.get("status") == "candidate_only", (
        f"application family {family['id']} must remain candidate-only until target validation"
    )
    for app in family.get("examples", []):
        assert app.get("name") and app.get("source"), (
            f"application example in {family['id']} needs a name and upstream source"
        )

# Keep the scheduler's SMP claim honest: serial stepping is not parallel execution.
SCHEDULER = ROOT / "kernel/core/scheduler.cpp"
scheduler_source = SCHEDULER.read_text(encoding="utf-8")
parallel_signature = 'extern "C" uint32_t chimera_sched_run_parallel('
assert parallel_signature in scheduler_source, f"missing parallel scheduler entry: {SCHEDULER}"
parallel_body = scheduler_source.split(parallel_signature, 1)[1].split("\n}", 1)[0]
assert "chimera_sched_run_once(" not in parallel_body, (
    "run_parallel must not disguise serial callback stepping as SMP"
)
assert "chimera_sched_run_serial_range(" not in parallel_body, (
    "run_parallel must not delegate to the serial stepping helper"
)
assert "return 0;" in parallel_body, (
    "parallel dispatch must fail closed until independent AP workers are implemented"
)

# Parallel-for must not disguise serial chunk iteration as concurrent execution.
PARALLEL_SOURCE = ROOT / "kernel/core/parallel.cpp"
parallel_source = PARALLEL_SOURCE.read_text(encoding="utf-8")
assert "if (workers > 1) return 0;" in parallel_source, (
    "multi-worker parallel_for requests must fail closed until AP-backed dispatch exists"
)
assert "for (uint32_t i = begin; i < end; ++i)" in parallel_source, (
    "single-worker fallback must be explicit and reviewable"
)

# Installer media is a data payload, not proof of a native ring-3 init process.
KORONOS_SOURCE = ROOT / "kernel/core/koronos.cpp"
koronos_source = KORONOS_SOURCE.read_text(encoding="utf-8")
assert "Installer handoff blocked: installation image is data and no native USER_INIT_ELF module was staged" in koronos_source, (
    "installer payload without a native init ELF must remain explicitly blocked"
)

# A dedicated Koronos ABI init artifact is compiled separately from test probes.
NATIVE_INIT = ROOT / "kernel/userspace/native_init.c"
NATIVE_LINKER = ROOT / "kernel/userspace/native_init_linker.ld"
NATIVE_BUILD = ROOT / "kernel/build-koronos.sh"
assert NATIVE_INIT.is_file() and NATIVE_LINKER.is_file(), "native init source/linker layout missing"
native_source = NATIVE_INIT.read_text(encoding="utf-8")
assert 'int $0x80' in native_source and "CHM_SYS_GETPID" in native_source and "CHM_SYS_WRITE" in native_source, (
    "native init must use the CPL3 gate and Koronos native syscall ABI"
)
assert "VFS mounting, storage" in native_source and "service supervision and desktop readiness" in native_source, (
    "native init must not overclaim unfinished runtime readiness"
)
build_source = NATIVE_BUILD.read_text(encoding="utf-8")
assert "kernel/userspace/native_init.c" in build_source and "native-init-$target.elf" in build_source, (
    "build must compile production init independently from candidate probes"
)

app_count = sum(len(family.get("examples", [])) for family in families)
print(f"cross-OS contracts PASS: {len(os_entries)} OS families, "
      f"{len(compat['cpu_profiles'])} CPU profiles, {len(setting_ids)} settings, "
      f"{len(families)} app families/{app_count} candidate apps, "
      f"{len(driver['pipeline'])} driver-assistant stages (policy only)")
