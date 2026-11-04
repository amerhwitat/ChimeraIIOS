import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("dd",Path(__file__).parents[2]/"services/network/directory-discovery.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_domain_validation(self):
  with self.assertRaises(ValueError):m.discover("bad domain")
 def test_domain_shape(self):
  self.assertTrue(m.DOMAIN.fullmatch("corp.example.com"));self.assertFalse(m.DOMAIN.fullmatch("-bad.example"))
if __name__=="__main__":unittest.main()
