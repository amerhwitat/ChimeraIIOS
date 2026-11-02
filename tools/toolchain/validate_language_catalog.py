#!/usr/bin/env python3
"""Validate the shared language/compiler/assembler/disassembler capability catalog."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "toolchains" / "language-toolchain-catalog.json"


def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def validate(data):
    assert data.get("schema") == "CHM-LANGUAGE-TOOLCHAIN-1"
    assert data.get("version") == 1
    policy = data["policy"]
    assert policy["catalog_is_not_installation_proof"] is True
    assert policy["install_mode"] == "explicit-user-request"
    assert policy["proprietary_tools"] == "external-installation-only"
    names = [entry["name"] for entry in data["languages"]]
    assert len(names) == len(set(names)), "duplicate language names"
    assert len(names) >= 40, "language catalog unexpectedly incomplete"
    for entry in data["languages"]:
        assert entry["name"].strip()
        assert entry["compiler"] or entry["interpreter"], entry["name"]
        assert entry["execution_model"].strip()
        assert entry["package_hints"]
        assert entry["capability_status"] == "available-when-provider-installed"
        assert entry["native_abi_claim"] is False
    for section in ("assemblers", "disassemblers"):
        entries = data[section]
        assert entries, f"empty {section}"
        tool_names = [entry["name"] for entry in entries]
        assert len(tool_names) == len(set(tool_names)), f"duplicate {section} entries"
        for entry in entries:
            assert entry["commands"] and entry["targets"] and entry["formats"]
            assert entry["license"]
            if entry["license"] == "proprietary-external":
                assert entry.get("distribution") == "external-installation-only"
    profiles = data["install_profiles"]
    assert {"native-core", "systems", "managed", "scripting",
            "functional-scientific", "assembly-analysis", "webassembly"}.issubset(profiles)
    for profile in profiles.values():
        assert profile["description"].strip()
        assert {"apt", "dnf", "pacman"}.issubset(profile["packages"])
        for packages in profile["packages"].values():
            assert packages and len(packages) == len(set(packages))
    assert {"GNU ld", "LLVM lld", "wasm-ld"}.issubset(set(data["linkers"]))
    assert {"x86_64", "aarch64", "riscv64", "wasm32", "chimera8192"}.issubset(
        set(data["cross_targets"])
    )


if __name__ == "__main__":
    catalog = load_catalog()
    validate(catalog)
    print(
        "language toolchain catalog validated: "
        f"{len(catalog['languages'])} languages, "
        f"{len(catalog['assemblers'])} assemblers, "
        f"{len(catalog['disassemblers'])} disassemblers"
    )
