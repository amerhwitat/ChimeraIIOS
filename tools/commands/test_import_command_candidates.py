import json, tempfile, unittest
from pathlib import Path
from tools.commands.import_command_candidates import build, NATIVE, COMMON
class ImportTests(unittest.TestCase):
 def test_native_only_allowlisted(self):
  data=build({"linux_bash":["echo","curl","mystery"]},{},{})
  rows={x["normalized_name"]:x for x in data["commands"]}
  self.assertTrue(rows["echo"]["execution_allowed"])
  self.assertFalse(rows["curl"]["execution_allowed"])
  self.assertFalse(rows["mystery"]["execution_allowed"])
 def test_preserves_unknown_for_runtime_learning(self):
  data=build({"custom":["futurecmd"]},{},{})
  row=next(x for x in data["commands"] if x["name"]=="futurecmd")
  self.assertEqual(row["learning"]["state"],"unresolved")
  self.assertEqual(row["dispatch"],"defer-to-runtime-learning")
 def test_common_catalog_is_nonempty(self):
  self.assertGreaterEqual(len(COMMON), 30)
  self.assertTrue(NATIVE.issubset(COMMON))
if __name__ == "__main__": unittest.main()
