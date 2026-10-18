import json, tempfile, unittest
from pathlib import Path
from tools.isa.isa_candidate_router import rank, queue_unresolved
class ISACandidateRouterTests(unittest.TestCase):
 def test_finds_source_backed_add_without_promoting_execution(self):
  data={"instructions":[{"architecture":"riscv32","mnemonic":"ADD","form_id":"fixture:add","encoding_status":"sourced-mask-verified","execution_status":"not-implemented","source_ref":"https://example.invalid/spec"}]}
  result=rank("riscv add",data,5)
  self.assertEqual(result[0]["mnemonic"],"ADD")
  self.assertFalse(result[0]["execution_allowed"])
  self.assertIn("conformance",result[0]["next_step"])
 def test_empty_catalog_query_is_queued_without_raw_query(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"pending.jsonl"
   queue_unresolved("z80 private operand text",{"instructions":[]},path)
   text=path.read_text(encoding="utf-8")
   row=json.loads(text.splitlines()[0])
   self.assertEqual(row["status"],"pending")
   self.assertNotIn("private",text)
   self.assertNotIn("operand",text)
   self.assertEqual(row["candidate_hint"],"z80")
 def test_known_architecture_and_mnemonic_not_queued(self):
  data={"instructions":[{"architecture":"riscv32/riscv64","mnemonic":"ADD","form_id":"fixture"}]}
  with tempfile.TemporaryDirectory() as tmp:
   self.assertIsNone(queue_unresolved("riscv add",data,Path(tmp)/"pending.jsonl"))
 def test_empty_catalog_is_safe(self): self.assertEqual(rank("unknown",{"instructions":[]}),[])
if __name__=="__main__":unittest.main()
