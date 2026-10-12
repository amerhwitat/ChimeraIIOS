import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class BootPipelineContractTest(unittest.TestCase):
 def test_static_boot_contract(self):
  r=subprocess.run([sys.executable,str(ROOT/"tools/boot/validate_boot_pipeline.py")],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)

 def test_userspace_handoff_limitations_are_reported_truthfully(self):
  source=(ROOT/"kernel/core/koronos.cpp").read_text()
  self.assertIn("userspace execution is not implemented",source)
  self.assertIn("Installer UI userspace unavailable: execution handoff is not implemented",source)
  self.assertIn("No installer userspace process was launched",source)
  self.assertNotIn('console_write("[LIVE] Runtime handoff queued")',source)
  self.assertNotIn('console_write("[INST] Installer UI service initialized")',source)
 def test_stage_order_contract(self):
  m=json.loads((ROOT/"boot/boot-artwork-manifest.json").read_text())
  self.assertEqual(list(m["boot_chain"]),["spitfire","jasper","grub","menus","koronos","aurora"])
if __name__=="__main__":unittest.main()
