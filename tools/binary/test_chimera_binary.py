import struct,unittest
from chimera_binary import identify,validate_ncb,NCB_HEADER,NCB_SECTION,NCB_HEADER_SIZE
class BinaryTests(unittest.TestCase):
 def test_elf(self):
  b=bytearray(64);b[:6]=b"\x7fELF\x02\x01";struct.pack_into("<H",b,18,183);self.assertEqual(identify(b)["architecture"],"AArch64")
 def test_pe(self):
  b=bytearray(0x100);b[:2]=b"MZ";struct.pack_into("<I",b,0x3c,0x80);b[0x80:0x84]=b"PE\0\0";struct.pack_into("<H",b,0x84,0x8664);self.assertEqual(identify(b)["architecture"],"x86-64")
 def test_wasm_script_unknown(self):
  self.assertEqual(identify(b"\0asm\x01\0\0\0")["format"],"WebAssembly");self.assertEqual(identify(b"#!/bin/sh\n")["kind"],"script");self.assertEqual(identify(b"junk","x.exe")["format"],"unknown/data")
 def test_ncb_header_sections(self):
  name=b".text\0".ljust(16,b"\0");code=b"abcd";table=NCB_HEADER_SIZE;off=table+NCB_SECTION.size
  h=NCB_HEADER.pack(b"NCB1",1,NCB_HEADER_SIZE,0,7,8192,1,off,table,off+4,65536,1<<20,0x10000,0)
  s=NCB_SECTION.pack(name,1,off,4,4,4);v=validate_ncb(h+s+code);self.assertEqual(v["word_bits"],8192);self.assertEqual(v["sections"][0]["name"],".text")
 def test_writer_roundtrip(self):
  import json,os,tempfile
  from build_ncb import build
  with tempfile.TemporaryDirectory() as d:
   m={"word_bits":8192,"isa_id":7,"sections":[{"name":".text","flags":5,"hex":"01020304","alignment":4},{"name":".bss","flags":6,"hex":"","memory_size":128}]}
   mp=os.path.join(d,"m.json");op=os.path.join(d,"app.ncb")
   with open(mp,"w") as f:json.dump(m,f)
   result=build(mp,op);self.assertEqual(result["word_bits"],8192)
   self.assertEqual(validate_ncb(open(op,"rb").read())["sections"][1]["memory_size"],128)
 def test_bad_ncb_rejected(self):
  with self.assertRaises(ValueError):validate_ncb(b"NCB1")
if __name__=="__main__":unittest.main()
