import tempfile,unittest
from pathlib import Path
from chimera_swap import SwapArea,SwapError,PAGE
class SwapTests(unittest.TestCase):
 def test_roundtrip_clear_bounds(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"swap.bin";s=SwapArea.create(p,2);data=bytes(i%251 for i in range(PAGE));s.write_page(1,data);self.assertEqual(s.read_page(1),data);s.clear(1)
   with self.assertRaises(SwapError):s.read_page(1)
   with self.assertRaises(SwapError):s.read_page(2)
   s.close()
 def test_corruption(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"swap.bin";s=SwapArea.create(p,1);s.write_page(0,b"x"*PAGE);s.close()
   with open(p,"r+b") as f:f.seek(HEADER.size+META.size);f.write(b"y")
   s=SwapArea(p)
   with self.assertRaises(SwapError):s.read_page(0)
   s.close()
from chimera_swap import HEADER,META
if __name__=="__main__":unittest.main()
