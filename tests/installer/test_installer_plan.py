#!/usr/bin/env python3
"""Regression tests for the non-destructive Chimera II installer planner."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "installer"))

from installer_plan import build_plan, load_capability_catalog  # noqa: E402


def test_linux_workstation_plan_is_safe() -> None:
    plan = build_plan("linux", "workstation")
    assert plan["schema"] == "chimera-ii-installer-plan"
    assert plan["platform"] == "linux"
    assert plan["profile"] == "workstation"
    assert plan["dry_run"] is True
    assert plan["destructive_storage"] is False
    assert plan["storage_policy"]["partition_table"] == "GPT"
    assert "hardware_inventory" in plan["steps"]
    assert "driver_plan" in plan["steps"]
    assert "aurora_wayland_optional" in plan["steps"]


def test_windows_server_plan_and_catalog() -> None:
    catalog = load_capability_catalog(ROOT / "tools" / "installer" / "installer_capabilities.json")
    assert isinstance(catalog, dict)
    plan = build_plan("windows", "server", dry_run=True)
    assert plan["platform"] == "windows"
    assert plan["profile"] == "server"
    assert plan["destructive_storage"] is False
    assert plan["driver_sources"] == ["windows_driver_catalog"]
    assert "network_services" in plan["steps"]
    assert "storage_services" in plan["steps"]


if __name__ == "__main__":
    tests = [test_linux_workstation_plan_is_safe, test_windows_server_plan_and_catalog]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} installer planner tests")
