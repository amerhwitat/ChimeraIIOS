#!/usr/bin/env python3
"""TDD tests for the Chimera II installer planning layer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "installer"))
from installer_plan import build_plan, load_capability_catalog


class InstallerPlanTests(unittest.TestCase):
    def test_catalog_has_required_cross_platform_capabilities(self):
        catalog = load_capability_catalog(ROOT / "tools/installer/installer_capabilities.json")
        names = {x["id"] for x in catalog["capabilities"]}
        for required in {
            "uefi_boot", "pci", "usb", "network", "graphics", "nvme",
            "storage_raid", "partitioning", "lvm", "filesystem", "wayland",
            "firmware", "windows_driver_catalog"
        }:
            self.assertIn(required, names)

    def test_safe_default_plan_is_non_destructive(self):
        plan = build_plan("linux", "interactive", dry_run=True)
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["destructive_storage"])
        self.assertIn("hardware_inventory", plan["steps"])
        self.assertIn("driver_plan", plan["steps"])
        self.assertIn("storage_plan", plan["steps"])

    def test_server_profile_enables_storage_and_network_services(self):
        plan = build_plan("linux", "server", dry_run=True)
        self.assertIn("network_services", plan["steps"])
        self.assertIn("storage_services", plan["steps"])
        self.assertEqual(plan["profile"], "server")

    def test_windows_plan_is_metadata_only_outside_windows(self):
        plan = build_plan("windows", "workstation", dry_run=True)
        self.assertEqual(plan["platform"], "windows")
        self.assertIn("windows_driver_catalog", plan["driver_sources"])


if __name__ == "__main__":
    unittest.main()
