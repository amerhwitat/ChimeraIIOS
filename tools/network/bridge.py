#!/usr/bin/env python3
"""Opt-in LAN presence bridge. UDP broadcast only; never scans Internet hosts."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import socket,json,threading,time
P=8768;B=38768;MAG=b"CHIMERA2-PRESENCE\n";peers={};lock=threading.Lock()
def rx():
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(("",B));s.settimeout(1)
 while 1:
  try:
   d,a=s.recvfrom(65535)
   if d.startswith(MAG):
    p=json.loads(d[len(MAG):]);p["address"]=a[0];p["lastSeen"]=time.time()
    with lock:peers[p["id"]]=p
  except Exception:pass
def announce(p):
 p["lastSeen"]=time.time()
 with lock:peers[p["id"]]=p
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1);s.sendto(MAG+json.dumps(p).encode(),("255.255.255.255",B));s.close()
class H(BaseHTTPRequestHandler):
 def do_POST(self):
  if self.path!="/lan/discover":self.send_error(404);return
  n=int(self.headers.get("Content-Length","0"));p=json.loads(self.rfile.read(n) or b"{}");announce(p)
  with lock:q=[x for x in peers.values() if x["id"]!=p.get("id") and time.time()-x.get("lastSeen",0)<20]
  d=json.dumps({"peers":q,"scope":"local-broadcast-only"}).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.end_headers();self.wfile.write(d)
if __name__=="__main__":
 threading.Thread(target=rx,daemon=True).start();print("Chimera Network bridge on 127.0.0.1:8768");ThreadingHTTPServer(("127.0.0.1",P),H).serve_forever()
