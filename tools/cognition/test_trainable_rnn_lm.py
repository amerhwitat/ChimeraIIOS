import tempfile, unittest
from pathlib import Path
from tools.cognition.trainable_rnn_lm import CharRNN
class TrainableRNNTests(unittest.TestCase):
 def test_training_changes_weights_and_scores_text(self):
  corpus=["echo list files","riscv add instruction","echo list files","riscv add instruction"]
  model=CharRNN(sorted(set("".join(corpus)+" \n")),hidden=6,seed=11)
  before=model.score("echo list files")
  losses=model.train(corpus,epochs=8,learning_rate=0.05)
  after=model.score("echo list files")
  self.assertTrue(all(x>=0 for x in losses))
  self.assertNotEqual(before,after)
  self.assertTrue(after > -100)
 def test_model_round_trip(self):
  corpus=["alpha command","beta instruction","alpha command"]
  model=CharRNN(sorted(set("".join(corpus)+" \n")),hidden=5)
  model.train(corpus,epochs=2)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"model.json";model.save(path,{"test":True});loaded=CharRNN.load(path)
   self.assertAlmostEqual(model.score("alpha command"),loaded.score("alpha command"),places=8)
 def test_rejects_malformed_weight_dimensions(self):
  import json
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"model.json"
   model=CharRNN(sorted(set("alpha beta \n")),hidden=4)
   model.save(path)
   data=json.loads(path.read_text(encoding="utf-8"))
   data["Wxh"][0].pop()
   path.write_text(json.dumps(data),encoding="utf-8")
   with self.assertRaises(ValueError):CharRNN.load(path)
 def test_rejects_nonfinite_weights(self):
  import json
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"model.json"
   model=CharRNN(sorted(set("alpha beta \n")),hidden=4)
   model.save(path)
   data=json.loads(path.read_text(encoding="utf-8"))
   data["Why"][0][0]=float("nan")
   path.write_text(json.dumps(data),encoding="utf-8")
   with self.assertRaises(ValueError):CharRNN.load(path)
 def test_rejects_unknown_schema(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"bad.json";path.write_text('{"schema":"wrong"}')
   with self.assertRaises(ValueError):CharRNN.load(path)
if __name__=="__main__":unittest.main()
