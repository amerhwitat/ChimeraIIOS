#!/usr/bin/env python3
import importlib.util,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
smb=load("smb_browse",pathlib.Path("tools/network/chimera-smb-browse.py"))
class NetworkHelperTests(unittest.TestCase):
 def test_smb_rejects_invalid_host(self):
  with self.assertRaises(ValueError):smb.shares("host/share")
 def test_smb_requires_authentication(self):
  with self.assertRaises(ValueError):smb.shares("fileserver.example")
 def test_smb_rejects_shell_metacharacters(self):
  with self.assertRaises(ValueError):smb.shares("server;touch /tmp/pwned",user="alice")
 def test_domain_join_source_has_no_password_cli_option(self):
  source=(ROOT/"tools/network/chimera-domain-join.py").read_text()
  self.assertNotIn("--password",source)
  self.assertIn("realm",source)
if __name__=="__main__":unittest.main()
