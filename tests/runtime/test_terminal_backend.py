import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("terminal_backend",ROOT/"tools/runtime/chimera-terminal-backend.py")
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)

class TerminalServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.workspace=Path(self.temp.name)
        self.service=MODULE.TerminalService(self.workspace,False)
        self.payload={"session":"test-session","shell":"bash"}
    def tearDown(self):self.temp.cleanup()
    def run_cmd(self,command):return self.service.execute({**self.payload,"command":command})
    def test_pwd_cd_and_workspace_files(self):
        self.assertEqual(self.run_cmd("pwd")["cwd"],str(self.workspace))
        (self.workspace/"docs").mkdir();self.run_cmd("cd docs")
        self.assertEqual(self.run_cmd("pwd")["cwd"],str(self.workspace/"docs"))
        self.run_cmd("touch notes.txt")
        self.assertEqual(self.run_cmd("ls")["output"],"notes.txt")
        self.assertEqual(self.run_cmd("cat notes.txt")["output"],"")
    def test_traversal_operators_and_arbitrary_code_rejected(self):
        with self.assertRaises(ValueError):self.run_cmd("cat ../../etc/passwd")
        with self.assertRaises(ValueError):self.run_cmd("echo hi; cat /etc/passwd")
        with self.assertRaises(ValueError):self.run_cmd("python3 -c 'print(1)'")
    def test_shell_aliases(self):
        self.assertEqual(self.service.execute({**self.payload,"shell":"cmd","command":"ver"})["output"],MODULE.platform.platform())
        self.assertEqual(self.service.execute({**self.payload,"shell":"powershell","command":"Get-Location"})["cwd"],str(self.workspace))
    def test_unsafe_shell_requires_explicit_flag(self):
        with self.assertRaises(ValueError):self.run_cmd("bash -lc 'echo unsafe'")
        if MODULE.shutil.which("bash"):
            unsafe=MODULE.TerminalService(self.workspace,True)
            result=unsafe.execute({**self.payload,"command":"echo LOCAL_SHELL_OK"})
            self.assertIn("LOCAL_SHELL_OK",result["output"]);self.assertEqual(result["mode"],"local-shell")
    def test_history_is_session_scoped(self):
        self.run_cmd("echo one");self.run_cmd("echo two")
        self.assertIn("echo one",self.run_cmd("history")["output"])
        other=self.service.execute({"session":"other","shell":"bash","command":"history"})
        self.assertNotIn("echo one",other["output"])
if __name__=="__main__":unittest.main()
