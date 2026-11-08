#!/usr/bin/env python3
"""Static regression guard for the fail-closed native production release gate."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
workflow = (ROOT / ".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")

required_contract = (
    "steps.userspace_gate.outputs.accepted != 'true' || steps.production_gate.outputs.accepted != 'true'",
    '"filesystem_syscall_contract": "filesystem-syscall-contract.json"',
    '"native_x_server": "native-x-server.json"',
    'data.get("etc_os_release_open") is True',
    'data.get("etc_os_release_read") is True',
    'data.get("etc_os_release_close") is True',
    'data.get("tmp_writable") is True',
    'data.get("x_server_started") is True',
    'data.get("gui_interaction_passed") is True',
    'data.get("cold_boot_persisted") is True',
    'data.get("repair_postcondition") is True',
    'data.get("overlap_intervals", 0) > 0',
    'data.get("providers_tested") == 28',
    'data.get("source_catalogue_unique_command_count") == 855',
    'data.get("source_catalogue_candidate_only_count") == 818',
    'data.get("source_catalogue_unverified_provider_count") == 0',
    'required_architectures = {"x86_64", "i686", "armel", "aarch64", "armv7", "riscv64", "ppc64le", "s390x"}',
    'failed_checks = [name for name in required if not checks.get(name, False)]',
    "steps.production_gate.outputs.accepted == 'true'",
    '"same_target_init_elf_sha256_across_firmware"',
    '"init_elf_sha256"',
)
missing = [item for item in required_contract if item not in workflow]
if missing:
    raise SystemExit("FAIL: production release gate contract missing: " + "; ".join(missing))
print("PASS: production release publication requires complete filesystem, native X server, architecture, persistence, recovery, SMP and terminal evidence")
