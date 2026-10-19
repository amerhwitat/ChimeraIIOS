import json, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from ai.koronos_chat import ChatSession, OpenAICompatibleBackend, BackendUnavailable

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.payload=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        b=json.dumps({"choices":[{"message":{"content":"test reply"}}]}).encode()
        self.send_response(200); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

class T(unittest.TestCase):
    def setUp(self):
        self.s=HTTPServer(("127.0.0.1",0),H); self.t=threading.Thread(target=self.s.serve_forever,daemon=True); self.t.start()
        self.b=OpenAICompatibleBackend(f"http://127.0.0.1:{self.s.server_port}","test",2); self.c=ChatSession()
    def tearDown(self): self.s.shutdown(); self.s.server_close(); self.t.join(timeout=2)
    def test_roundtrip(self):
        self.assertEqual(self.b.reply(self.c,"hello"),"test reply")
        self.assertEqual([x["role"] for x in self.c.history],["user","assistant"])
    def test_bounded_history(self):
        for i in range(20): self.c.add("user",str(i))
        self.assertEqual(len(self.c.history),12)
    def test_reject_remote_http(self):
        with self.assertRaises(ValueError): OpenAICompatibleBackend("http://outside.invalid","x")
    def test_reject_long_input(self):
        with self.assertRaises(ValueError): self.c.add("user","x"*4097)
if __name__=="__main__": unittest.main()
