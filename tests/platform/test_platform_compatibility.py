import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class PlatformCompatibilityTests(unittest.TestCase):
    def test_contract_covers_both_editions_and_all_host_families(self):
        p=json.loads((ROOT/"system/platform/compatibility-contract.json").read_text())
        self.assertEqual(set(p["editions"]), {"hosted","baremetal"})
        self.assertEqual(set(p["host_os_matrix"]), {"linux","freebsd","windows","macos"})
    def test_baremetal_is_host_kernel_independent(self):
        p=json.loads((ROOT/"system/baremetal/compatibility-matrix.json").read_text())
        self.assertFalse(p["runtime_policy"]["host_os_required_at_runtime"])
        self.assertFalse(p["runtime_policy"]["host_kernel_drivers_reused"])
    def test_no_foreign_driver_loading_claim(self):
        p=json.loads((ROOT/"system/platform/compatibility-contract.json").read_text())
        self.assertTrue(any("does not claim full" in x for x in p["non_claims"]))
    def test_vendor_cli_catalog_is_safe_by_default(self):
        p=json.loads((ROOT/"network/vendor-cli-compatibility.json").read_text())
        self.assertFalse(p["safety"]["shell_execution"])
        self.assertEqual(p["safety"]["default_mode"],"plan-only")
        self.assertIn("cisco_ios",p["vendors"])
        self.assertIn("juniper_junos",p["vendors"])

if __name__ == "__main__": unittest.main()
