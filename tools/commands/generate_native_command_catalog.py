#!/usr/bin/env python3
"""Build a normalized native command catalogue from the real source catalogues.

Every union entry is emitted. An entry is marked implemented only when a real
provider function exists in src/chimera-command-compat/chimera-cmd.c, is listed
in the multicall install script, and is declared in the engineering provider
manifest. Catalog metadata such as "native-source-implemented" is never treated
as proof of implementation. Official conformance counts are never modified.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUTS = {
    "command_list": ROOT / "system/commands/chimera-command-list.json",
    "isa_coverage": ROOT / "system/commands/command-isa-coverage.json",
    "capabilities": ROOT / "system/commands/command-runtime-capabilities.json",
    "candidates": ROOT / "system/commands/native-command-candidates.json",
    "ss64": ROOT / "system/commands/ss64-command-catalog.json",
    "policy": ROOT / "system/commands/compatibility-binary-policy.json",
    "providers": ROOT / "system/commands/native-provider-engineering.json",
    "source": ROOT / "src/chimera-command-compat/chimera-cmd.c",
    "install_script": ROOT / "tools/build-chimera-command-compat.sh",
    "official_isa": ROOT / "isa/generated/universal-instruction-catalog.json",
}
DEFAULT_OUTPUT = ROOT / "system/commands/native-command-catalog.json"

NAMESPACE_PRECEDENCE = (
    "native_chimera", "linux_bash", "linux_posix_shells", "macos_core", "macos",
    "windows_cmd_core", "windows_cmd", "powershell_core", "powershell",
    "vbscript_core", "vbscript", "sql_server_core", "sql_server",
    "compatibility_commands", "metadata", "driver_hardware_catalog",
)
NO_PROVIDER_REASON = (
    "no native provider in multicall source; catalog metadata is not implementation"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_inputs(inputs: dict[str, Path]) -> dict:
    command_list = load(inputs["command_list"])
    coverage = load(inputs["isa_coverage"])
    capabilities = load(inputs["capabilities"])
    candidates = load(inputs["candidates"])
    ss64 = load(inputs["ss64"])

    by_name: dict[str, dict] = {}

    def touch(name: str, source: str, platform: str | None = None,
              url: str | None = None) -> None:
        if not name:
            return
        row = by_name.setdefault(name, {
            "name": name,
            "catalog_sources": [],
            "platforms": [],
            "source_urls": [],
        })
        if source not in row["catalog_sources"]:
            row["catalog_sources"].append(source)
        if platform and platform not in row["platforms"]:
            row["platforms"].append(platform)
        if url and url not in row["source_urls"]:
            row["source_urls"].append(url)

    for key, value in command_list.items():
        if isinstance(value, list) and key not in ("sources", "platforms"):
            for name in value:
                if isinstance(name, str):
                    touch(name, "chimera-command-list.json", key)

    for row in coverage["commands"]:
        for platform in row.get("platforms", []):
            touch(row["name"], "command-isa-coverage.json", platform)

    for row in capabilities["commands"]:
        for platform in row.get("platforms", []):
            touch(row["name"], "command-runtime-capabilities.json", platform)

    for row in candidates["commands"]:
        for platform in row.get("platforms", []) or []:
            touch(row["name"], "native-command-candidates.json", platform)

    for platform, doc in ss64["platforms"].items():
        for row in doc["commands"]:
            touch(row["name"], "ss64-command-catalog.json", platform,
                  row.get("source"))

    return {
        "rows": by_name,
        "counts": {
            "chimera_command_list_unique": len({
                name for key, value in command_list.items()
                if isinstance(value, list) and key not in ("sources", "platforms")
                for name in value if isinstance(name, str)
            }),
            "command_isa_coverage_unique": len(coverage["commands"]),
            "command_runtime_capabilities_records": len(capabilities["commands"]),
            "native_command_candidates_records": len(candidates["commands"]),
            "ss64_index_entries": sum(
                len(doc["commands"]) for doc in ss64["platforms"].values()
            ),
            "isa_architectures_in_coverage": len(coverage["architectures"]),
            "union_unique_commands": len(by_name),
        },
        "coverage_by_name": {row["name"]: row for row in coverage["commands"]},
        "capabilities_by_name": {row["name"]: row for row in capabilities["commands"]},
        "candidates_by_name": {row["name"]: row for row in candidates["commands"]},
    }


def real_providers(inputs: dict[str, Path]) -> tuple[list[dict], dict]:
    provider_doc = load(inputs["providers"])
    source = inputs["source"].read_text(encoding="utf-8")
    install = inputs["install_script"].read_text(encoding="utf-8")

    names = [row["name"] for row in provider_doc["providers"]
             if row.get("implementation") == "native"]
    specs = provider_doc["provider_specs"]

    if len(names) != len(set(names)):
        raise SystemExit("duplicate provider names in engineering manifest")
    if set(names) != set(specs):
        raise SystemExit("provider_specs must cover exactly the declared providers")

    alias_match = re.search(r"NATIVE_COMMANDS=\((.*?)\)\n", install, re.S)
    if not alias_match:
        raise SystemExit("NATIVE_COMMANDS array not found in install script")
    aliases = set(alias_match.group(1).split())

    verified = []
    for name in names:
        function = specs[name]["function"]
        if f'strcmp(cmd, "{name}")' not in source:
            raise SystemExit(f"provider has no real dispatch in source: {name}")
        if f"static int {function}(" not in source:
            raise SystemExit(f"provider function not found in source: {function}")
        if name not in aliases:
            raise SystemExit(f"provider alias not installed by build script: {name}")
        verified.append({
            "name": name,
            "provider_id": f"native:{function}",
            "function": function,
            "spec": specs[name],
        })

    return verified, provider_doc


def namespace_for(platforms: list[str]) -> str:
    for candidate in NAMESPACE_PRECEDENCE:
        if candidate in platforms:
            return candidate
    return platforms[0] if platforms else "unclassified"


def official_snapshot(path: Path) -> dict:
    doc = load(path)
    coverage = doc["coverage"]
    return {
        "source": "isa/generated/universal-instruction-catalog.json",
        "status": doc.get("status", "not-run"),
        "conformance_tested": coverage["conformance_tested"],
        "not_implemented": coverage["not_implemented"],
        "conformance_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for key, path in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", type=Path, default=path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    inputs = {key: getattr(args, key) for key in DEFAULT_INPUTS}
    for key, path in inputs.items():
        if not path.is_file():
            raise SystemExit(f"missing input for {key}: {path}")

    collected = collect_inputs(inputs)
    providers, provider_doc = real_providers(inputs)
    by_name = {provider["name"]: provider for provider in providers}

    policy = load(inputs["policy"])
    build_targets = policy.get("isa_execution", {}).get("build_targets")
    if not build_targets:
        build_targets = ["x86_64", "aarch64", "riscv64"]

    records = []
    for name in sorted(collected["rows"]):
        raw = collected["rows"][name]
        platform_list = raw["platforms"]
        provider = by_name.get(name)

        if provider:
            spec = provider["spec"]
            record = {
                "name": name,
                "namespace": namespace_for(platform_list),
                "isa_targets": list(build_targets),
                "isa_target_status": "cross-build-targets-verified-by-build-matrix",
                "operands": spec["operands"],
                "options": spec["options"],
                "implementation": provider["provider_id"],
                "implementation_details": {
                    "status": "native_provider",
                    "multicall_alias": name,
                    "function": provider["function"],
                    "source": "src/chimera-command-compat/chimera-cmd.c",
                    "semantics": next(
                        row["semantics"] for row in provider_doc["providers"]
                        if row["name"] == name
                    ),
                },
                "implementation_reason": None,
                "effects_on_registers": [],
                "register_effects_status": "not-isa-visible-userspace-command",
                "exit_codes": spec["exit_codes"],
                "side_effects": spec["side_effects"],
                "permission_flags": spec["permission_flags"],
            }
        else:
            capability = collected["capabilities_by_name"].get(name, {})
            reason = NO_PROVIDER_REASON
            if capability.get("mode") == "compatibility-provider-required":
                reason += "; required provider: " + str(capability.get("provider"))
            elif capability.get("mode") == "native-provider-required":
                reason += "; native provider still required"
            record = {
                "name": name,
                "namespace": namespace_for(platform_list),
                "isa_targets": [],
                "isa_target_status": "no-per-command-isa-mapping-in-source-catalog",
                "operands": [],
                "options": [],
                "implementation": "not_implemented",
                "implementation_details": {"status": "not_implemented"},
                "implementation_reason": reason,
                "effects_on_registers": [],
                "register_effects_status": "not-implemented-no-isa-backend",
                "exit_codes": "unknown-not-implemented",
                "side_effects": "unknown-not-implemented",
                "permission_flags": 0,
            }

        record["catalog_sources"] = raw["catalog_sources"]
        record["platforms"] = platform_list
        record["source_urls"] = raw["source_urls"]
        records.append(record)

    implemented = sum(1 for row in records if row["implementation"] != "not_implemented")
    doc = {
        "schema": "CHM-NATIVE-COMMAND-CATALOG-1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "engineering-partial",
        "policy": ("A row is implemented only with a verified native provider function "
                   "in the multicall source and an installed alias. Catalog metadata "
                   "never marks a row implemented."),
        "full_conformance": False,
        "conformance_claim": False,
        "production_acceptance": False,
        "official_status_snapshot": official_snapshot(inputs["official_isa"]),
        "input_counts": collected["counts"],
        "provider_manifest": "system/commands/native-provider-engineering.json",
        "provider_count": len(providers),
        "implemented_count": implemented,
        "not_implemented_count": len(records) - implemented,
        "record_count": len(records),
        "records": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "union_unique_commands": collected["counts"]["union_unique_commands"],
        "coverage_unique_commands": collected["counts"]["command_isa_coverage_unique"],
        "capability_records": collected["counts"]["command_runtime_capabilities_records"],
        "candidate_records": collected["counts"]["native_command_candidates_records"],
        "providers": len(providers),
        "not_implemented": len(records) - implemented,
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
