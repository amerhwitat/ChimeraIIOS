import unittest
from tools.cognition.koronos_chat import ChatSession, OpenAICompatibleBackend

class ChatTests(unittest.TestCase):
    def test_history_is_bounded(self):
        session = ChatSession()
        for index in range(20):
            session.add("user", str(index))
        self.assertEqual(len(session.history), 12)

    def test_only_user_and_assistant_roles(self):
        with self.assertRaises(ValueError):
            ChatSession().add("system", "not allowed")

    def test_empty_and_oversized_messages_rejected(self):
        with self.assertRaises(ValueError):
            ChatSession().add("user", "  ")
        with self.assertRaises(ValueError):
            ChatSession().add("user", "x" * 4097)

    def test_remote_plain_http_rejected(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleBackend("http://remote.invalid", "model")

    def test_loopback_http_allowed(self):
        backend = OpenAICompatibleBackend("http://127.0.0.1:8080", "model")
        self.assertTrue(backend.url.endswith("/v1/chat/completions"))

if __name__ == "__main__":
    unittest.main()
