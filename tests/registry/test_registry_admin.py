#!/usr/bin/env python3
import base64,importlib.util,json,pathlib,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("registry_admin",ROOT/"tools/registry/registry_admin.py")
admin=importlib.util.module_from_spec(spec);spec.loader.exec_module(admin)
class RegistryAdminTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();base=pathlib.Path(self.tmp.name)
  admin.GLOBAL_ROOT=base/"global";admin.USER_ROOT=base/"user";admin.DEFAULTS=base/"defaults";admin.DEFAULTS.mkdir()
  for h in admin.HIVES:
   (admin.DEFAULTS/(h+".defaults.json")).write_bytes((ROOT/"system/registry"/(h+".defaults.json")).read_bytes())
 def tearDown(self):self.tmp.cleanup()
 def test_environment_update_and_binary_hive(self):
  before=admin.load_hive("environment");g=before["generation"]
  admin.set_value("environment","environment.locale","string","en_GB.UTF-8")
  after=admin.load_hive("environment")
  self.assertEqual(after["generation"],g+1)
  self.assertEqual(next(x["value"] for x in after["entries"] if x["path"]=="environment.locale"),"en_GB.UTF-8")
  self.assertEqual(admin.registry_hive.verify(admin.hive_path(admin.USER_ROOT,"environment").read_bytes())["generation"],g+1)
 def test_machine_requires_admin(self):
  with patch.object(admin.os,"geteuid",return_value=1000):
   with self.assertRaises(PermissionError):admin.set_value("machine","machine.identity.profile","string","test")
 def test_stale_generation_rejected(self):
  stale=admin.load_hive("environment")
  admin.set_value("environment","environment.locale","string","fr_FR.UTF-8")
  with self.assertRaises(RuntimeError):admin.commit({"environment":stale})
 def test_prepared_journal_replays_idempotently(self):
  obj=admin.load_hive("environment");obj["generation"]+=1
  src=(json.dumps(obj)+"\n").encode();binary=admin.registry_hive.encode(obj)
  tx={"schema":"CHM-REGISTRY-TXN-1","phase":"prepared","hives":[{"name":"environment","source":base64.b64encode(src).decode(),"binary":base64.b64encode(binary).decode()}]}
  root=admin.USER_ROOT;root.mkdir(parents=True,exist_ok=True)
  (root/"transaction.json").write_text(json.dumps(tx))
  admin.recover_locked(root)
  self.assertFalse((root/"transaction.json").exists())
  self.assertEqual(admin.load_hive("environment")["generation"],obj["generation"])
if __name__=="__main__":unittest.main()
