import unittest
from tools.isa.isa_candidate_router import rank
class ISACandidateRouterTests(unittest.TestCase):
 def test_finds_source_backed_add_without_promoting_execution(self):
  data={"instructions":[{"architecture":"riscv32","mnemonic":"ADD","form_id":"fixture:add","encoding_status":"sourced-mask-verified","execution_status":"not-implemented","source_ref":"https://example.invalid/spec"}]}
  result=rank("riscv add",data,5)
  self.assertEqual(result[0]["mnemonic"],"ADD")
  self.assertFalse(result[0]["execution_allowed"])
  self.assertIn("conformance",result[0]["next_step"])
 def test_empty_catalog_is_safe(self): self.assertEqual(rank("unknown",{"instructions":[]}),[])
if __name__=="__main__":unittest.main()
