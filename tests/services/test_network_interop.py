import importlib.util,unittest,os,tempfile,contextlib,io,sys
from types import SimpleNamespace
from unittest import mock
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
 def test_smb_registry_settings_are_allowlisted(self):
  original=smb.get_value
  try:
   smb.get_value=lambda hive,key,default: "NT1" if "minimum_protocol" in key else "WORKGROUP"
   with self.assertRaises(ValueError):smb.smb_client_settings()
   smb.get_value=lambda hive,key,default: "SMB2_10" if "minimum_protocol" in key else "bad;workgroup"
   with self.assertRaises(ValueError):smb.smb_client_settings()
  finally:smb.get_value=original
 def test_ldap_uri_validation(self):
  self.assertTrue(directory.valid_ldap_uri("ldaps://ldap.corp.example:636"));self.assertTrue(directory.valid_ldap_uri("ldap://ldap.corp.example:389"))
  self.assertFalse(directory.valid_ldap_uri("ldap://ldap.corp.example:99999"));self.assertFalse(directory.valid_ldap_uri("ldap://user:pass@ldap.corp.example"))
 @mock.patch.object(directory.shutil, "which", side_effect=lambda name: "/usr/bin/pkexec" if name == "pkexec" else "/usr/sbin/realm")
 @mock.patch.object(directory, "run", side_effect=[
        SimpleNamespace(returncode=0, stdout="", stderr=""),
        SimpleNamespace(returncode=0, stdout="joined", stderr="")
    ])
 def test_ad_join_elevates_with_existing_private_ticket_cache(self, mocked, _which):
        old_argv = sys.argv
        with tempfile.NamedTemporaryFile() as cache:
            os.chmod(cache.name, 0o600)
            try:
                sys.argv = ["directoryctl.py", "join", "example.org", "--user",
                            "admin@example.org", "--elevate"]
                with mock.patch.dict(os.environ, {"KRB5CCNAME": "FILE:" + cache.name}):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(directory.main(), 0)
            finally:
                sys.argv = old_argv
        command = mocked.call_args_list[1].args[0]
        self.assertEqual(command[:3], ["/usr/bin/pkexec", "/usr/bin/env",
                                       "KRB5CCNAME=FILE:" + cache.name])
        self.assertIn("--no-password", command)
        self.assertNotIn("--password", command)
if __name__=="__main__":unittest.main()
