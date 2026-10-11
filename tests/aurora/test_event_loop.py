import json, subprocess, sys, unittest, socket, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class AuroraEventLoopTests(unittest.TestCase):
    def run_events(self, events):
        return subprocess.run([sys.executable,str(ROOT/"desktop/aurora/aurora_event_loop.py")],
            input="".join(json.dumps(x)+"\n" for x in events),capture_output=True,text=True,check=True)
    def test_click_double_triple_and_titlebar(self):
        r=self.run_events([
          {"surface":"file","click_count":1},
          {"surface":"file","click_count":2},
          {"surface":"text","click_count":3},
          {"surface":"window-titlebar","click_count":2,"maximized":False},
          {"surface":"window-titlebar","click_count":2,"maximized":True}
        ])
        actions=[json.loads(x)["request"]["action"] for x in r.stdout.splitlines()]
        self.assertEqual(actions,["select","open","select-all","maximize","restore"])
    def test_compatibility_and_keyboard_context_menu(self):
        r=self.run_events([
          {"surface":"folder","kind":"compatibility","click_count":2},
          {"surface":"file","kind":"keyboard","key":"Shift+F10"}
        ])
        requests=[json.loads(x)["request"] for x in r.stdout.splitlines()]
        self.assertEqual(requests[0]["mode"],"compatibility")
        self.assertEqual(requests[1]["action"],"context-menu")
    def test_invalid_surface_is_rejected(self):
        r=self.run_events([{"surface":"arbitrary","click_count":1}])
        self.assertIn("rejected",r.stderr)
    def test_local_socket_message_loop(self):
        with __import__("tempfile").TemporaryDirectory() as td:
            path=Path(td)/"events.sock"
            proc=subprocess.Popen([sys.executable,str(ROOT/"desktop/aurora/aurora_event_loop.py"),"--socket",str(path)],
                                  stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            try:
                for _ in range(100):
                    if path.exists(): break
                    if proc.poll() is not None: self.fail("event loop exited before creating socket")
                    time.sleep(0.02)
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                    client.settimeout(2)
                    client.connect(str(path))
                    client.sendall(b'{"surface":"window-titlebar","click_count":2,"maximized":false}\n')
                    response=json.loads(client.makefile("r",encoding="utf-8").readline())
                    self.assertEqual(response["request"]["action"],"maximize")
            finally:
                proc.terminate()
                try: proc.wait(timeout=2)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=2)
if __name__=="__main__": unittest.main()
