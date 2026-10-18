import json,tempfile,unittest
from pathlib import Path
from tools.cognition.train_command_isa_rnn import corpus_from
from tools.cognition.trainable_rnn_lm import CharRNN
class CommandISARnnTrainingTests(unittest.TestCase):
 def test_balanced_corpus_preserves_command_and_execution_status(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);cmd=root/"commands.json";isa=root/"isa.json"
   cmd.write_text(json.dumps({"counts":{"total":1},"commands":[{"name":"echo","status":"native-implemented","provider":"native","target":"linux"}]}),encoding="utf-8")
   isa.write_text(json.dumps({"instructions":[{"architecture":"riscv32","mnemonic":"ADD","form_id":"rv32i.add","encoding_status":"sourced-mask-verified","execution_status":"not-implemented"}]}),encoding="utf-8")
   rows,c,i=corpus_from(cmd,isa)
   self.assertTrue(any("command echo" in x and "native-implemented" in x for x in rows))
   self.assertTrue(any("instruction riscv32 ADD" in x and "not-implemented" in x for x in rows))
   self.assertEqual(c["counts"]["total"],1);self.assertEqual(len(i["instructions"]),1)
 def test_sampling_is_deterministic_and_bounded(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);cmd=root/"commands.json";isa=root/"isa.json"
   cmd.write_text(json.dumps({"commands":[{"name":f"cmd{i}","status":"candidate"} for i in range(500)]}),encoding="utf-8")
   isa.write_text(json.dumps({"instructions":[{"architecture":"riscv","mnemonic":f"OP{i}","form_id":str(i)} for i in range(700)]}),encoding="utf-8")
   a,_,_=corpus_from(cmd,isa,limit=25);b,_,_=corpus_from(cmd,isa,limit=25)
   self.assertEqual(a,b);self.assertEqual(len(a),50)
if __name__=="__main__":unittest.main()
