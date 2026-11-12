import importlib.util, json, pathlib, subprocess, unittest
ROOT=pathlib.Path(__file__).resolve().parents[3]
SPEC=importlib.util.spec_from_file_location("c64demo",ROOT/"retro/commodore/create-c64-demo.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class RetroMediaTests(unittest.TestCase):
 def test_basic_program(self):
  data=MOD.build_program("HELLO CHIMERA")
  self.assertEqual(data[:2],b"\x01\x08"); self.assertEqual(data[4],10); self.assertEqual(data[6],0x99); self.assertEqual(int.from_bytes(data[2:4],"little"),0x0801+len(data)-4); self.assertTrue(data.endswith(b"\0\0"))
 def test_catalogue(self):
  d=json.loads((ROOT/"retro/commodore/machines.json").read_text()); ids={x["id"] for x in d["machines"]}
  self.assertEqual(ids,{"amiga-a500","amiga-a2000","amiga-a4000","commodore-c64"})
  self.assertFalse(any(x["firmware_required"] for x in d["machines"] if x["family"]=="Amiga"))
 def test_help(self):
  p=subprocess.run(["bash",str(ROOT/"retro/commodore/launch-machine.sh"),"--help"],check=True,capture_output=True,text=True)
  self.assertIn("amiga-a500",p.stdout)
if __name__=="__main__": unittest.main()
