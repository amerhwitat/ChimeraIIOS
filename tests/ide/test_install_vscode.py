import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("install_vscode",ROOT/"tools/ide/install-vscode.py")
MODULE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
class VSCodeInstallerTests(unittest.TestCase):
 def test_windows_winget_plan(self):
  plan=MODULE.install_plan("Windows",which=lambda x:x=="winget")
  self.assertIn("Microsoft.VisualStudioCode",plan)
 def test_macos_brew_plan(self):
  plan=MODULE.install_plan("Darwin",which=lambda x:x=="brew")
  self.assertEqual(plan,["brew","install","--cask","visual-studio-code"])
 def test_linux_requires_package_manager(self):
  with self.assertRaises(RuntimeError): MODULE.install_plan("Linux",which=lambda x:False)
if __name__=="__main__": unittest.main()
