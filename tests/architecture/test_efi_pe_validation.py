import importlib.util, pathlib, struct, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("validate_efi_pe",ROOT/"tools"/"validate_efi_pe.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
def fixture(machine=0xaa64,magic=0x20b,subsystem=10,entry=0x1000):
 pe=0x80; osz=112 if magic==0x20b else 96; sh=pe+24+osz; raw=0x200
 d=bytearray(0x300); d[:2]=b"MZ"; struct.pack_into("<I",d,0x3c,pe); d[pe:pe+4]=b"PE\0\0"
 struct.pack_into("<HHIIIHH",d,pe+4,machine,1,0,0,0,osz,0x2022)
 o=pe+24; struct.pack_into("<H",d,o,magic); struct.pack_into("<I",d,o+16,entry)
 struct.pack_into("<II",d,o+32,0x1000,0x200); struct.pack_into("<I",d,o+56,0x2000)
 struct.pack_into("<I",d,o+60,0x200); struct.pack_into("<H",d,o+68,subsystem)
 struct.pack_into("<8sIIIIIIHHI",d,sh,b".text\0\0\0",0x100,0x1000,0x100,raw,0,0,0,0,0x60000020)
 d[raw:raw+4]=b"TEST"; return bytes(d)
class TestEFIPE(unittest.TestCase):
 def test_accepts_aarch64_application_fixture(self): self.assertEqual(MOD.validate_pe(fixture(),"aarch64")["subsystem"],10)
 def test_rejects_machine_mismatch(self):
  with self.assertRaisesRegex(MOD.PEValidationError,"COFF machine"): MOD.validate_pe(fixture(machine=0x8664),"aarch64")
 def test_rejects_wrong_subsystem(self):
  with self.assertRaisesRegex(MOD.PEValidationError,"EFI_APPLICATION"): MOD.validate_pe(fixture(subsystem=3),"aarch64")
 def test_rejects_wrong_optional_magic(self):
  with self.assertRaisesRegex(MOD.PEValidationError,"optional-header magic"): MOD.validate_pe(fixture(magic=0x10b),"aarch64")
 def test_rejects_nonexecutable_entry(self):
  with self.assertRaisesRegex(MOD.PEValidationError,"entry point"): MOD.validate_pe(fixture(entry=0x5000),"aarch64")
 def test_rejects_truncated_input(self):
  with self.assertRaises(MOD.PEValidationError): MOD.validate_pe(b"MZ","aarch64")
if __name__=="__main__": unittest.main()
