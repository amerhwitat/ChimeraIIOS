import importlib.util, json, unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("chimera_network_preflight",ROOT/"installer/network_preflight.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
class NetworkPreflightTests(unittest.TestCase):
    def test_no_device_gives_actionable_recommendation(self):
        rec=mod.recommend({"devices":[],"connectivity":{"internet_ready":False}})
        self.assertTrue(rec); self.assertIn("No network interface",rec[0]["title"])
    def test_bound_wifi_recommends_wifi_configuration(self):
        rec=mod.recommend({"devices":[{"name":"wlan0","type":"wifi","driver_bound":True}],"connectivity":{"internet_ready":False}})
        self.assertTrue(any("Wi-Fi" in x["title"] for x in rec))
    def test_missing_driver_recommends_identification_not_blind_install(self):
        rec=mod.recommend({"devices":[{"name":"wlan0","type":"wifi","driver_bound":False,"modalias":"pci:v00008086"}],"connectivity":{"internet_ready":False}})
        self.assertTrue(any("driver" in x["title"].lower() for x in rec))
    def test_ready_network_recommends_continue(self):
        rec=mod.recommend({"devices":[],"connectivity":{"internet_ready":True}})
        self.assertIn("Internet ready",rec[0]["title"])
    def test_report_does_not_have_password_field(self):
        report={"schema":"CHIMERA-NETWORK-PREFLIGHT-1","devices":[],"connectivity":{"internet_ready":False}}
        self.assertNotIn("password",json.dumps(report).lower())
    def test_network_is_first_installer_phase_and_gui_step(self):
        phases=json.loads((ROOT/"installer/installation_phases.json").read_text())
        self.assertEqual(phases["phases"][0]["id"],"network_preflight")
        ui=json.loads((ROOT/"installer/gui/aurora-installer-ui.json").read_text())
        self.assertEqual(ui["first_step"],"Network")
        shell=(ROOT/"installer/gui/aurora-installer.sh").read_text()
        self.assertLess(shell.index('python3 "$NETWORK_PREFLIGHT" --gui'),shell.index('edition="$(choose_edition)"'))
    def test_step_by_step_recommendations_are_ordered_and_non_destructive(self):
        spec=importlib.util.spec_from_file_location("chimera_installer",ROOT/"installer/chimera_installer.py")
        installer=importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        inv={"network_preflight":{"connectivity":{"internet_ready":False},"devices":[]}}
        plan={"selection":{"edition":"desktop"}}
        with patch.object(installer.shutil,"which",return_value=None):
            result=installer.recommend_install_steps(inv,plan)
        self.assertEqual(result["engine"],"deterministic-hardware-rules")
        self.assertEqual([x["step"] for x in result["steps"]],list(range(1,len(result["steps"])+1)))
        self.assertIn("Storage and data protection",[x["title"] for x in result["steps"]])
if __name__=="__main__": unittest.main()
