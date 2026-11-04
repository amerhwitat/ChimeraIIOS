#!/usr/bin/env python3
"""Loopback-only Aurora registry editor; registryd enforces Unix peer credentials."""
import hmac,json,os,pathlib,secrets,socket,tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
HOST="127.0.0.1";PORT=int(os.environ.get("CHIMERA_REGISTRY_UI_PORT","8765"));SOCKET=os.environ.get("CHIMERA_REGISTRY_SOCKET","/run/chimera/registry.sock");HTML=pathlib.Path(os.environ.get("CHIMERA_REGISTRY_EDITOR_HTML","/usr/share/chimera/aurora/registry-editor.html"))
TOKEN_PATH=pathlib.Path(os.environ.get("XDG_RUNTIME_DIR",f"/run/user/{os.getuid()}"))/"chimera-registry-editor.token"
TOKEN=""
def call_registry(payload):
 data=(json.dumps(payload,separators=(",",":"))+"\n").encode()
 if len(data)>1<<20:raise ValueError("request exceeds 1 MiB")
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as peer:
  peer.settimeout(5);peer.connect(SOCKET);peer.sendall(data);chunks=bytearray()
  while len(chunks)<=1<<20:
   part=peer.recv(65536)
   if not part:break
   chunks.extend(part)
   if b"\n" in part:break
 if len(chunks)>1<<20:raise ValueError("response exceeds 1 MiB")
 return json.loads(bytes(chunks).split(b"\n",1)[0])
class Handler(BaseHTTPRequestHandler):
 server_version="ChimeraRegistryUI/1"
 def _origin_ok(self):
  if self.headers.get("Host") not in (f"127.0.0.1:{PORT}",f"localhost:{PORT}"):return False
  return self.headers.get("Origin") in (None,f"http://127.0.0.1:{PORT}",f"http://localhost:{PORT}")
 def _authorized(self):
  return bool(TOKEN) and hmac.compare_digest(self.headers.get("X-Chimera-Token",""),TOKEN)
 def _send(self,code,payload,ctype="application/json; charset=utf-8"):
  body=payload if isinstance(payload,bytes) else json.dumps(payload).encode();self.send_response(code);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if not self._origin_ok():return self._send(403,{"ok":False,"error":"origin-denied"})
  if self.path=="/":
   try:return self._send(200,HTML.read_bytes(),"text/html; charset=utf-8")
   except OSError as exc:return self._send(503,{"ok":False,"error":str(exc)})
  if not self._authorized():return self._send(403,{"ok":False,"error":"editor-token-required"})\n  if self.path.startswith("/api/registry/"):
   hive=self.path.rsplit("/",1)[-1]
   if hive not in ("machine","environment","kernel"):return self._send(404,{"ok":False,"error":"unknown-hive"})
   req={"op":"read","hive":hive}
  elif self.path=="/api/registry":req={"op":"list"}
  else:return self._send(404,{"ok":False,"error":"not-found"})
  try:
   result=call_registry(req);return self._send(200 if result.get("ok") else 403,result)
  except (OSError,ValueError) as exc:return self._send(503,{"ok":False,"error":str(exc)})
 def do_POST(self):
  if not self._origin_ok():return self._send(403,{"ok":False,"error":"origin-denied"})
  if self.path!="/api/registry/entry":return self._send(404,{"ok":False,"error":"not-found"})
  if self.headers.get("Content-Type","").split(";",1)[0].strip().lower()!="application/json":return self._send(415,{"ok":False,"error":"application-json-required"})
  try:
   size=int(self.headers.get("Content-Length","-1"))
   if size<2 or size>1<<20:raise ValueError("invalid request size")
   req=json.loads(self.rfile.read(size))
   if not isinstance(req,dict) or req.get("op") not in ("set","delete"):raise ValueError("invalid registry operation")
   result=call_registry(req);return self._send(200 if result.get("ok") else 403,result)
  except (OSError,ValueError) as exc:return self._send(400,{"ok":False,"error":str(exc)})
 def log_message(self,fmt,*args):pass
def main():
 global TOKEN
 TOKEN=secrets.token_urlsafe(32)
 TOKEN_PATH.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix="registry-editor-",dir=str(TOKEN_PATH.parent))
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,"w",encoding="utf-8") as stream:stream.write(TOKEN)
  os.replace(name,TOKEN_PATH)
  server=ThreadingHTTPServer((HOST,PORT),Handler)
  try:server.serve_forever()
  finally:server.server_close()
 finally:
  try:os.unlink(name)
  except FileNotFoundError:pass
  try:TOKEN_PATH.unlink()
  except FileNotFoundError:pass
if __name__=="__main__":main()
