import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parents[2]
spec=importlib.util.spec_from_file_location("mount_image",ROOT/"services/storage/mount-image.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class OpticalMediaTests(unittest.TestCase):
 def image(self,descriptor,sequence=None):
  data=bytearray(17*2048)
  data[16*2048]=1
  data[16*2048+1:16*2048+6]=descriptor
  if sequence:
   data[17*2048+1:17*2048+6]=sequence
  f=tempfile.NamedTemporaryFile(delete=False);f.write(data);f.close();self.addCleanup(Path(f.name).unlink,missing_ok=True);return f.name
 def test_iso9660_descriptor(self):
  self.assertTrue(m.validate_image(self.image(b"CD001")).is_file())
 def test_udf_recognition_sequence(self):
  self.assertTrue(m.validate_image(self.image(b"BEA01",b"NSR02")).is_file())
 def test_rejects_incomplete_udf_and_non_optical_devices(self):
  with self.assertRaises(ValueError):m.validate_image(self.image(b"BEA01"))
  self.assertTrue(m.valid_optical_device("/dev/sr0"));self.assertFalse(m.valid_optical_device("/dev/sda"))
if __name__=="__main__":unittest.main()
