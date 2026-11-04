import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parents[2];spec=importlib.util.spec_from_file_location("rd",ROOT/"services/registry/registryd.py");rd=importlib.util.module_from_spec(spec);spec.loader.exec_module(rd)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();rd.ROOT=Path(self.tmp.name);rd.TOOL=ROOT/"tools/registry/registry_hive.py"
  for h in rd.HIVES:(rd.ROOT/(h+".json")).write_text(json.dumps(json.loads((ROOT/"system/registry"/(h+".defaults.json")).read_text())))
 def tearDown(self):self.tmp.cleanup()
 def test_transaction_and_generation(self):
  r=rd._handle({"op":"set","hive":"environment","path":"environment.locale","type":"string","value":"en_GB.UTF-8","generation":1},True)
  self.assertEqual(r["generation"],2);self.assertEqual(rd._read("environment")["generation"],2);self.assertTrue((rd.ROOT/"environment.hive").is_file())
  with self.assertRaises(RuntimeError):rd._handle({"op":"set","hive":"environment","path":"environment.locale","type":"string","value":"x","generation":1},True)
 def test_protected_and_namespace(self):
  with self.assertRaises(PermissionError):rd._handle({"op":"set","hive":"machine","path":"cpu.feature_override.enabled","type":"bool","value":False,"generation":1},True)
  with self.assertRaises(ValueError):rd._handle({"op":"set","hive":"environment","path":"kernel.debug.log_level","type":"u32","value":1,"generation":1},True)
if __name__=="__main__":unittest.main()
