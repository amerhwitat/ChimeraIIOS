#!/usr/bin/env python3
import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/"tools/isa/chimera_isa_convert.py"
DB=ROOT/"isa/isa_database.json"
class IsaConvertTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.db=json.loads(DB.read_text(encoding="utf-8"))
 def run_tool(self,*args): return subprocess.run([sys.executable,str(TOOL),*args],cwd=ROOT,text=True,capture_output=True)
 def test_every_architecture_has_exactly_one_profile(self):
  profiles=self.db["execution_model"]["translation_profiles"]; ids={p["architecture"] for p in profiles}
  self.assertEqual(ids,{a[0] for a in self.db["architectures"]}); self.assertEqual(len(ids),len(profiles))
 def test_known_form_plans_semantic_ir_not_machine_code(self):
  r=self.run_tool("plan","x86-64","ADD"); self.assertEqual(r.returncode,0,r.stderr); p=json.loads(r.stdout)
  self.assertEqual(p["status"],"semantic-ir-plan-only"); self.assertFalse(p["machine_code_emitted"]); self.assertFalse(p["execution_verified"]); self.assertEqual(p["target"]["semantic_operation"],"add")
 def test_unknown_form_fails_closed(self):
  r=self.run_tool("plan","x86-64","INVENTED_OPCODE"); self.assertEqual(r.returncode,2); self.assertIn("no catalogued instruction form",r.stderr)
 def test_unmapped_form_fails_closed(self):
  r=self.run_tool("plan","chimera-c8192","TCONTRACT"); self.assertEqual(r.returncode,2); self.assertIn("no approved semantic-operation mapping",r.stderr)
 def test_compatibility_backend_is_not_guessed(self):
  r=self.run_tool("plan","x86-64","ADD","--mode","compatibility"); self.assertEqual(r.returncode,2); self.assertIn("compatibility backend unavailable",r.stderr)
 def test_inventory_command(self):
  r=self.run_tool("inventory"); self.assertEqual(r.returncode,0,r.stderr); d=json.loads(r.stdout)
  self.assertEqual(d["profile_count"],d["architecture_count"]); self.assertGreater(d["instruction_candidate_count"],0)
if __name__=="__main__": unittest.main()
