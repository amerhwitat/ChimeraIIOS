#!/usr/bin/env python3
import importlib.util, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("cpu_isa_target_map",ROOT/"tools/isa/map_cpu_isa.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class CpuIsaMapTests(unittest.TestCase):
 def test_full_catalogue_is_covered(self):
  db=json.loads((ROOT/"isa/isa_database.json").read_text())
  mapping=json.loads((ROOT/"isa/cpu_isa_target_map.json").read_text())
  self.assertEqual([],mod.validate(db,mapping))
  self.assertEqual({r[0] for r in db["architectures"]},{r["architecture"] for r in mapping["architectures"]})
 def test_all_cisc_map_to_c8192(self):
  m=json.loads((ROOT/"isa/cpu_isa_target_map.json").read_text())
  rows=[r for r in m["architectures"] if r["isa_class"] in ("CISC","CISC-extension")]
  self.assertTrue(rows)
  self.assertTrue(all(r["target"]=="chimera-c8192" for r in rows))
 def test_all_risc_map_to_r8192(self):
  m=json.loads((ROOT/"isa/cpu_isa_target_map.json").read_text())
  rows=[r for r in m["architectures"] if r["isa_class"] in ("RISC","RISC-extension")]
  self.assertTrue(rows)
  self.assertTrue(all(r["target"]=="chimera-r8192" for r in rows))
 def test_non_scalar_isa_families_are_not_misclassified(self):
  m=json.loads((ROOT/"isa/cpu_isa_target_map.json").read_text())
  for r in m["architectures"]:
   if r["isa_class"] not in ("CISC","RISC","CISC-extension","RISC-extension","custom"):
    self.assertNotIn(r["target"],("chimera-c8192","chimera-r8192"))
if __name__=="__main__": unittest.main()
