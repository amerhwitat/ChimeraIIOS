import unittest
from tools.commands.import_command_candidates import build
from tools.commands.command_candidate_router import rank
class RouterTests(unittest.TestCase):
 def test_ranking_never_authorizes_unknown_execution(self):
  catalog=build({"linux_bash":["echo","futurecmd"]},{},{})
  rows=rank("futurecmd",catalog,10)
  match=next(x for x in rows if x["name"]=="futurecmd")
  self.assertFalse(match["execution_allowed"])
  self.assertIn("do not execute",match["next_step"])
 def test_native_candidate_can_be_ranked(self):
  catalog=build({"linux_bash":["echo"]},{},{})
  rows=rank("echo",catalog,10)
  self.assertTrue(next(x for x in rows if x["name"]=="echo")["execution_allowed"])
if __name__ == "__main__": unittest.main()
