import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
DOC=ROOT/"docs"/"architecture"/"AARCH64_LINKER_ENTRY_ABI.md"
class TestAArch64LinkerContract(unittest.TestCase):
 def test_explicit_format_arch_and_entry_are_required(self):
  s=DOC.read_text(encoding="utf-8")
  for token in ("OUTPUT_FORMAT(elf64-littleaarch64)","OUTPUT_ARCH(aarch64)","ENTRY(kernel_entry)"): self.assertIn(token,s)
 def test_load_segments_and_wx_are_reviewed(self):
  s=DOC.read_text(encoding="utf-8")
  self.assertIn("PHDRS",s); self.assertIn("PT_LOAD",s); self.assertIn("W+X",s)
 def test_efi_artifact_is_separate(self):
  s=DOC.read_text(encoding="utf-8")
  self.assertIn("separate PE/COFF application",s); self.assertIn("not the kernel ELF",s)
if __name__=="__main__": unittest.main()
