import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("fhs",Path(__file__).parents[2]/"tools/filesystem/create-fhs-tree.py");fhs=importlib.util.module_from_spec(spec);spec.loader.exec_module(fhs)
class FhsTreeTests(unittest.TestCase):
 def test_fhs_permissions_and_preserves_existing_bin(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/"bin").mkdir();(r/"bin/legacy").write_text("keep");x=fhs.create(d)
   self.assertTrue((r/"usr/bin").is_dir());self.assertTrue((r/"bin/legacy").is_file());self.assertEqual((r/"tmp").stat().st_mode&0o7777,0o1777);self.assertEqual((r/"root").stat().st_mode&0o777,0o700);self.assertIn("/proc",x["mount_points"]);self.assertTrue((r/"var/run").is_symlink())
 def test_refuses_host_roots(self):
  for root in ("/","/usr","/etc"):
   with self.assertRaises(ValueError):fhs.create(root)
 def test_refuses_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/"etc").symlink_to("/tmp")
   with self.assertRaises(ValueError):fhs.create(d)
if __name__=="__main__":unittest.main()
