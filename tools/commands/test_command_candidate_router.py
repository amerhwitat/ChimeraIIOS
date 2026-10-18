import json, tempfile, unittest
from pathlib import Path
from tools.commands.import_command_candidates import build
from tools.commands.command_candidate_router import rank, queue_unresolved
class RouterTests(unittest.TestCase):
 def test_ranking_never_authorizes_unknown_execution(self):
  catalog=build({"linux_bash":["echo","futurecmd"]},{},{})
  rows=rank("futurecmd",catalog,10)
  match=next(x for x in rows if x["name"]=="futurecmd")
  self.assertFalse(match["execution_allowed"])
  self.assertIn("do not execute",match["next_step"])
 def test_unknown_query_is_queued_without_raw_arguments(self):
  catalog=build({"linux_bash":["echo","futurecmd"]},{},{})
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"pending.jsonl"
   result=queue_unresolved("futurecmd --secret value",catalog,path)
   row=json.loads(path.read_text(encoding="utf-8").splitlines()[0])
   self.assertEqual(result,str(path))
   self.assertEqual(row["command_token"],"futurecmd")
   self.assertNotIn("secret",path.read_text(encoding="utf-8"))
 def test_exact_native_query_is_not_queued(self):
  catalog=build({"linux_bash":["echo"]},{},{})
  with tempfile.TemporaryDirectory() as tmp:
   self.assertIsNone(queue_unresolved("echo",catalog,Path(tmp)/"pending.jsonl"))
 def test_native_candidate_can_be_ranked(self):
  catalog=build({"linux_bash":["echo"]},{},{})
  rows=rank("echo",catalog,10)
  self.assertTrue(next(x for x in rows if x["name"]=="echo")["execution_allowed"])
if __name__ == "__main__": unittest.main()
