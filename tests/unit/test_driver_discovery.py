#!/usr/bin/env python3
"""Static contract checks for PnP enumeration and driver catalog selection."""
import json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class DriverDiscoveryTests(unittest.TestCase):
 def test_catalog_has_upstreams_and_safe_statuses(self):
  data=json.loads((ROOT/"system/drivers/catalog.json").read_text(encoding="utf-8"));self.assertEqual(data["schema"],"CHIMERA-DRIVER-CATALOG-1");self.assertGreaterEqual(len(data["upstreams"]),4);self.assertIn("never compile or load remote source automatically",data["policy"]["install_policy"].lower());self.assertIn("metadata-only",data["policy"]["status_values"])
 def test_driver_manager_scores_ids_and_respects_bus(self):
  source=(ROOT/"kernel/core/driver.cpp").read_text(encoding="utf-8");self.assertIn("chimera_driver_best_match",source);self.assertIn("d->bus != bus",source);self.assertIn("score += 100",source);self.assertIn("d->subsystem_id != subsystem",source);self.assertNotIn("compatibility-adapter",source)
 def test_pci_inventory_records_subsystem_and_multifunction(self):
  source=(ROOT/"kernel/core/device.cpp").read_text(encoding="utf-8");self.assertIn("subsystem_vendor",source);self.assertIn("subsystem_device",source);self.assertIn("functions=(header&0x00800000u)?8u:1u",source);self.assertIn("CHIMERA_DEVICE_MAX",source)
 def test_sync_tool_only_indexes_never_executes(self):
  source=(ROOT/"tools/drivers/sync_upstream_catalog.py").read_text(encoding="utf-8");self.assertIn("recursive=1",source);self.assertIn("never downloads, compiles, installs",source);self.assertNotIn("subprocess.",source);self.assertNotIn("os.system(",source)
if __name__=="__main__":unittest.main()
