import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class BootPipelineContractTest(unittest.TestCase):
 def test_static_boot_contract(self):
  r=subprocess.run([sys.executable,str(ROOT/"tools/boot/validate_boot_pipeline.py")],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_interactive_menu_timeout_and_serial_input(self):
  for rel in ("boot/iso/grub.cfg","boot/jasper/jasper.cfg","boot/spitfire/spitfire-menu.cfg"):
   data=(ROOT/rel).read_text()
   self.assertRegex(data,r"(?m)^\s*set timeout=300\s*$",rel)
   self.assertRegex(data,r"(?m)^\s*serial --unit=0 --speed=115200\s*$",rel)
   self.assertRegex(data,r"(?m)^\s*terminal_input serial console\s*$",rel)
   self.assertRegex(data,r"(?m)^\s*terminal_output .*serial.*console\s*$",rel)
 def test_stage_order_contract(self):
  m=json.loads((ROOT/"boot/boot-artwork-manifest.json").read_text())
  self.assertEqual(list(m["boot_chain"]),["spitfire","jasper","grub","menus","koronos","aurora"])
if __name__=="__main__":unittest.main()
