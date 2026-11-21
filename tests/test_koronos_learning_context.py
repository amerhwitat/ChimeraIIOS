import importlib.util, json, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).parents[1]/"tools/runtime/koronos-learning-context.py"
spec=importlib.util.spec_from_file_location("learning_context",SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class ContextTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
  (self.root/"isa").mkdir(); (self.root/"system/commands").mkdir(parents=True)
  (self.root/"isa/isa_database.json").write_text(json.dumps({"version":"test","architecture_row":["id","class","family","word_bits","status","encoding_model","source_ref","instruction_forms"],"instruction_row":["architecture","mnemonic","form_id","operands","syntax","length_bits","value_bits","mask_bits"],"architectures":[["x86-64","CISC","x86",64,"verified","test","test",1],["riscv64","RISC","RISC-V",64,"catalog-only","test","test",0]],"instructions":[["x86-64","ADD","rr",["reg","reg"],"ADD r1,r2",32,"0","0"]]}),encoding="utf-8")
  (self.root/"system/commands/chimera-command-list.json").write_text(json.dumps({"schema_version":"3.0","linux_bash":["cat","grep"],"native_chimera":{"commands":["cat"]},"compatibility_commands":["grep","sed"]}),encoding="utf-8")
 def tearDown(self): self.tmp.cleanup()
 def test_modes_and_features(self):
  r=mod.build_context(self.root)
  self.assertEqual([p["mode"] for p in r["profiles"]],["native","compatibility"])
  self.assertIn("cpu_flags",r["profiles"][0]); self.assertIn("cat",r["profiles"][0]["commands"]); self.assertIn("grep",r["profiles"][1]["commands"])
 def test_no_unsupported_claims(self):
  r=mod.build_context(self.root); self.assertFalse(r["catalogs"]["instruction_catalog_is_exhaustive"]); self.assertFalse(r["safety"]["catalog_presence_implies_execution"])
 def test_invalid_mode(self):
  with self.assertRaises(ValueError): mod.build_context(self.root,"unknown")
if __name__=="__main__": unittest.main()
