import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
smb=load("smb_browse","services/network/smb-browse.py")
directory=load("directoryctl","services/network/directoryctl.py")
class NetworkInteropTests(unittest.TestCase):
 def test_smb_host_validation(self):
  self.assertTrue(smb.HOST.fullmatch("fileserver.corp.example"));self.assertFalse(smb.HOST.fullmatch("https://fileserver"))
  with self.assertRaises(ValueError):smb.browse("fileserver",kerberos=False)
 def test_ldap_uri_validation(self):
  self.assertTrue(directory.valid_ldap_uri("ldaps://ldap.corp.example:636"));self.assertTrue(directory.valid_ldap_uri("ldap://ldap.corp.example:389"))
  self.assertFalse(directory.valid_ldap_uri("ldap://ldap.corp.example:99999"));self.assertFalse(directory.valid_ldap_uri("ldap://user:pass@ldap.corp.example"))
if __name__=="__main__":unittest.main()
