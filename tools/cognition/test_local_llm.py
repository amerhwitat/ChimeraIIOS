import json,os,unittest
from unittest.mock import patch
from urllib.error import URLError
from tools.cognition.local_llm import rerank,_endpoint
class LocalLLMTests(unittest.TestCase):
 def test_remote_endpoint_rejected(self):
  with patch.dict(os.environ,{"CHIMERA_LLM_BASE_URL":"https://example.com/v1"}):
   with self.assertRaises(ValueError):_endpoint()
 def test_model_can_only_reorder_allowlisted_ids(self):
  body={"choices":[{"message":{"content":json.dumps({"ids":["b","a"]})}}]}
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def read(self,n):return json.dumps(body).encode()
  candidates=[{"id":"a","label":"Alpha"},{"id":"b","label":"Beta"}]
  with patch.dict(os.environ,{"CHIMERA_LLM_BASE_URL":"http://127.0.0.1:8080/v1","CHIMERA_LLM_MODEL":"test-model"}),patch("tools.cognition.local_llm.urllib.request.urlopen",return_value=Response()):
   ordered,meta=rerank("query",candidates,2)
  self.assertEqual([x["id"] for x in ordered],["b","a"])
  self.assertTrue(meta["validated"])
 def test_unknown_model_ids_fall_back(self):
  body={"choices":[{"message":{"content":json.dumps({"ids":["arbitrary"]})}}]}
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def read(self,n):return json.dumps(body).encode()
  candidates=[{"id":"safe","label":"Safe"}]
  with patch.dict(os.environ,{"CHIMERA_LLM_BASE_URL":"http://127.0.0.1:8080/v1"}),patch("tools.cognition.local_llm.urllib.request.urlopen",return_value=Response()):
   ordered,meta=rerank("query",candidates,1)
  self.assertEqual(ordered,candidates)
  self.assertFalse(meta["validated"])
  self.assertEqual(meta["mode"],"deterministic-fallback")
if __name__=="__main__":unittest.main()
