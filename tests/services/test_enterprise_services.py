import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class EnterpriseCatalogTests(unittest.TestCase):
    def test_catalog_has_optional_profiles_and_no_default_enabled_services(self):
        data=json.loads((ROOT/"installer/services/enterprise-services.json").read_text())
        self.assertTrue(data["security"]["install_requires_explicit_selection"])
        self.assertEqual(data["boot"]["default_enabled"], [])
        self.assertGreaterEqual(len(data["services"]), 15)
        self.assertTrue(all(s["boot_target"].endswith(".target") for s in data["services"]))
    def test_plan_only_does_not_modify_rootfs(self):
        with tempfile.TemporaryDirectory() as td:
            p=subprocess.run([sys.executable,str(ROOT/"tools/services/enterprise_service_installer.py"),
                              "--service","postgresql","--rootfs",td,"--cache",td+"/cache"],
                             capture_output=True,text=True,check=True)
            out=json.loads(p.stdout)
            self.assertEqual(out["services"][0]["id"],"postgresql")
            self.assertFalse((Path(td)/"etc/chimera/enterprise-services.plan.json").exists())
    def test_boot_and_installer_reference_catalog(self):
        boot=json.loads((ROOT/"boot/boot_protocol.json").read_text())
        plan=json.loads((ROOT/"installer/chimera-installer-plan.json").read_text())
        self.assertTrue(boot["enterprise_services"]["selection_required"])
        self.assertEqual(plan["optionalEnterpriseServices"]["defaultSelection"],[])
if __name__=="__main__": unittest.main()
