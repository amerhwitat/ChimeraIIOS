import json, os, socket, subprocess, sys, tempfile, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class NBitDaemonTests(unittest.TestCase):
    def test_get_set_and_validation_over_local_socket(self):
        with tempfile.TemporaryDirectory() as td:
            sock=Path(td)/"nbitd.sock"; config=Path(td)/"nbit.json"
            proc=subprocess.Popen([sys.executable,str(ROOT/"tools/runtime/chimera-nbitd.py"),
                "--socket",str(sock),"--config",str(config)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            try:
                for _ in range(100):
                    if sock.exists(): break
                    if proc.poll() is not None: self.fail("nbitd exited before creating socket")
                    time.sleep(.02)
                def request(obj):
                    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
                        s.settimeout(2);s.connect(str(sock))
                        s.sendall((json.dumps(obj)+"\n").encode())
                        f=s.makefile("r",encoding="utf-8");return json.loads(f.readline())
                self.assertTrue(request({"op":"get"})["ok"])
                result=request({"op":"set","bits":8193,"backend":"chimera-virtual","isa":"chimera-nbit"})
                self.assertTrue(result["ok"]);self.assertEqual(result["profile"]["selected_width_bits"],8193)
                self.assertEqual(json.loads(config.read_text())["guest_isa"],"chimera-nbit")
                self.assertFalse(request({"op":"set","bits":0,"backend":"auto","isa":"auto"})["ok"])
            finally:
                proc.terminate()
                try:proc.wait(timeout=2)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
if __name__=="__main__":unittest.main()
