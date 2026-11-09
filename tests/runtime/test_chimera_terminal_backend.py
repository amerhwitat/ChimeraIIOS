import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("aurora_bridge",ROOT/"tools/runtime/chimera-terminal-backend.py")
BRIDGE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BRIDGE)
class AuroraBridgeSafeModeTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name).resolve()
 def tearDown(self): self.tmp.cleanup()
 def run_safe(self,command,cwd=None,shell="bash"):return BRIDGE.safe_command(command,cwd or self.workspace,self.workspace,shell)
 def test_safe_workspace_basics(self):
  _,_,code,_=self.run_safe("mkdir project");self.assertEqual(code,0)
  _,_,code,_=self.run_safe("touch project/README.txt");self.assertEqual(code,0)
  out,_,_,_=self.run_safe("pwd");self.assertEqual(out,str(self.workspace))
  out,_,_,_=self.run_safe("ls project");self.assertEqual(out,"README.txt")
 def test_path_escape_is_rejected(self):
  outside=self.workspace.parent/"outside-secret.txt";outside.write_text("secret")
  try:
   _,err,code,_=self.run_safe("cat ../outside-secret.txt");self.assertNotEqual(code,0);self.assertIn("outside",err)
  finally:outside.unlink(missing_ok=True)
 def test_shell_metacharacters_are_not_executed_in_safe_mode(self):
  marker=self.workspace.parent/"must-not-exist";out,_,_,_=self.run_safe("echo hello; touch "+str(marker))
  self.assertEqual(out,"hello; touch "+str(marker));self.assertFalse(marker.exists())
 def test_shell_aliases(self):
  out,_,code,_=self.run_safe("Get-Location",shell="powershell");self.assertEqual(out,str(self.workspace));self.assertEqual(code,0)
  _,_,code,_=self.run_safe("dir",shell="cmd");self.assertEqual(code,0)
 def test_symlink_escape_is_rejected(self):
  outside=self.workspace.parent/"outside-dir";outside.mkdir();link=self.workspace/"escape"
  try:
   link.symlink_to(outside,target_is_directory=True)
   with self.assertRaises(PermissionError):BRIDGE.resolve_path("escape/secret.txt",self.workspace,self.workspace)
  finally:link.unlink(missing_ok=True);outside.rmdir()
if __name__=="__main__":unittest.main()
