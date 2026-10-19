import unittest
from ai.chat_session import ChatSession

class SessionTests(unittest.TestCase):
 def test_provider_round_trip(self):
  c=ChatSession(); result=c.reply("hello",lambda messages:"model reply")
  self.assertEqual(result,"model reply")
  self.assertEqual([m["role"] for m in c.history],["user","assistant"])
 def test_history_bound(self):
  c=ChatSession()
  for i in range(20): c.add("user",str(i))
  self.assertEqual(len(c.history),12)
 def test_missing_provider_fails_closed(self):
  with self.assertRaises(ValueError): ChatSession().reply("hello",None)
 def test_failed_provider_does_not_keep_user_turn(self):
  c=ChatSession()
  with self.assertRaises(RuntimeError): c.reply("hello",lambda _: (_ for _ in ()).throw(RuntimeError()))
  self.assertEqual(c.history,[])
if __name__=="__main__": unittest.main()
