import unittest
from services.llm_chat import ChatSession, OpenAICompatibleBackend

class ChatContractTests(unittest.TestCase):
 def test_history_is_bounded(self):
  c=ChatSession()
  for i in range(20): c.add("user",str(i))
  self.assertEqual(len(c.history),12)
  self.assertEqual(c.history[-1]["content"],"19")
 def test_invalid_role_rejected(self):
  with self.assertRaises(ValueError): ChatSession().add("system","bad")
 def test_empty_message_rejected(self):
  with self.assertRaises(ValueError): ChatSession().add("user"," ")
 def test_remote_plain_http_rejected(self):
  with self.assertRaises(ValueError): OpenAICompatibleBackend("http://remote.invalid","model")
if __name__=="__main__": unittest.main()
