#!/usr/bin/env python3
"""Small read-only CHMRG01 client for Linux user-space services."""
import json,os,socket
SOCKET=os.environ.get("CHIMERA_REGISTRY_SOCKET","/run/chimera/registry.sock")
def read_hive(hive,timeout=1.5):
 if hive not in ("machine","environment","kernel"):raise ValueError("unknown hive")
 request=(json.dumps({"op":"read","hive":hive},separators=(",",":"))+"\n").encode()
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as peer:
  peer.settimeout(timeout);peer.connect(SOCKET);peer.sendall(request);data=bytearray()
  while len(data)<=2<<20:
   part=peer.recv(65536)
   if not part:break
   data.extend(part)
   if b"\n" in part:break
 if len(data)>2<<20:raise ValueError("registry response too large")
 result=json.loads(bytes(data).split(b"\n",1)[0])
 if not result.get("ok"):raise PermissionError(result.get("message","registry read denied"))
 return result
def get_value(hive,path,default=None):
 try:
  result=read_hive(hive)
  for entry in result.get("entries",[]):
   if entry.get("path")==path:return entry.get("value",default)
 except (OSError,ValueError,KeyError,PermissionError):
  pass
 return default
