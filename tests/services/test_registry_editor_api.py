import email.message,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).parents[2]
spec=importlib.util.spec_from_file_location("registry_editor_api",ROOT/"services/registry/registry-editor-api.py")
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
class RegistryEditorApiTests(unittest.TestCase):
 def setUp(self):
  self.handler=api.Handler.__new__(api.Handler);self.handler.headers=email.message.Message()
  api.TOKEN="test-capability-token"
 def test_capability_required(self):
  self.assertFalse(self.handler._authorized())
  self.handler.headers["X-Chimera-Token"]="test-capability-token"
  self.assertTrue(self.handler._authorized())
  self.handler.headers["X-Chimera-Token"]="wrong"
  self.assertFalse(self.handler._authorized())
 def test_loopback_host_only(self):
  self.handler.headers["Host"]="127.0.0.1:8765"
  self.assertTrue(self.handler._origin_ok())
  self.handler.headers["Host"]="192.0.2.8:8765"
  self.assertFalse(self.handler._origin_ok())
 def test_mutations_require_same_origin(self):
  self.handler.headers["Host"]="127.0.0.1:8765"
  self.assertFalse(self.handler._origin_ok(require_origin=True))
  self.handler.headers["Origin"]="http://127.0.0.1:8765"
  self.assertTrue(self.handler._origin_ok(require_origin=True))
  self.handler.headers["Origin"]="https://attacker.example"
  self.assertFalse(self.handler._origin_ok(require_origin=True))
if __name__=="__main__":unittest.main()
