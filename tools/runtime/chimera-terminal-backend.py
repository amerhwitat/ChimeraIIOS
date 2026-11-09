#!/usr/bin/env python3
"""Loopback-only Aurora terminal bridge. Safe workspace mode is the default."""
from __future__ import annotations
import argparse, datetime as dt, getpass, json, os, secrets, shlex, shutil, socket, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

MAX_BODY=16384; MAX_COMMAND=4096; MAX_OUTPUT=65536
ALLOWED_ORIGIN="https://amerhwitat.github.io"
SHELLS=("bash","sh","zsh","fish","cmd","powershell","chimera")
SESSIONS={}; RATE={}; LOCK=threading.Lock()

def within_workspace(path:Path,workspace:Path)->Path:
 resolved=path.resolve()
 try: resolved.relative_to(workspace.resolve())
 except ValueError: raise PermissionError("path is outside the configured workspace")
 return resolved
def resolve_path(arg:str,cwd:Path,workspace:Path)->Path:
 raw=Path(arg).expanduser(); return within_workspace(raw if raw.is_absolute() else cwd/raw,workspace)
def safe_command(command:str,cwd:Path,workspace:Path,shell:str):
 try: args=shlex.split(command,posix=(shell not in ("cmd","powershell")))
 except ValueError as exc: return "",str(exc),2,cwd
 if not args:return "","",0,cwd
 cmd=args.pop(0).lower()
 aliases={"powershell":{"get-location":"pwd","set-location":"cd","get-childitem":"ls","get-content":"cat","write-output":"echo","write-host":"echo","clear-host":"clear","get-command":"which","get-date":"date"},"cmd":{"dir":"ls","type":"cat","cls":"clear","ver":"uname","where":"which"}}
 cmd=aliases.get(shell,{}).get(cmd,cmd)
 try:
  if cmd in ("help","man"):return "Safe bridge commands: pwd, cd, ls/dir, cat/type, echo, whoami, hostname, uname, date, env, which, mkdir, touch, rm, clear, exit. Files are confined to the configured workspace.","",0,cwd
  if cmd=="pwd":return str(cwd),"",0,cwd
  if cmd=="cd":
   target=resolve_path(args[0] if args else str(workspace),cwd,workspace)
   if not target.is_dir():return "",f"cd: not a directory: {target}",1,cwd
   return "","",0,target
  if cmd in ("ls","dir"):
   target=resolve_path(args[0],cwd,workspace) if args else cwd
   if not target.is_dir():return "",f"ls: not a directory: {target}",1,cwd
   return "\n".join(sorted(p.name+("/" if p.is_dir() else "") for p in target.iterdir())),"",0,cwd
  if cmd in ("cat","type","get-content"):
   if not args:return "","usage: cat FILE",2,cwd
   target=resolve_path(args[0],cwd,workspace)
   if not target.is_file():return "",f"cat: not a file: {target}",1,cwd
   if target.stat().st_size>MAX_OUTPUT:return "","cat: file exceeds safe output limit",1,cwd
   return target.read_text(encoding="utf-8",errors="replace"),"",0,cwd
  if cmd in ("echo","write-output","write-host","printf"):return " ".join(args),"",0,cwd
  if cmd=="whoami":return getpass.getuser(),"",0,cwd
  if cmd=="hostname":return socket.gethostname(),"",0,cwd
  if cmd=="uname":
   import platform
   return f"{platform.system()} {platform.machine()}","",0,cwd
  if cmd in ("date","get-date"):return dt.datetime.now().astimezone().isoformat(),"",0,cwd
  if cmd in ("env","set"):
   keys=("HOME","USER","USERNAME","SHELL","PATH","LANG")
   return "\n".join(f"{k}={os.environ.get(k,'')}" for k in keys),"",0,cwd
  if cmd in ("which","where","get-command"):
   if not args:return "","usage: which COMMAND",2,cwd
   found=shutil.which(args[0]); return found or f"{args[0]}: not found",("" if found else "not found"),(0 if found else 1),cwd
  if cmd=="mkdir":
   if not args:return "","usage: mkdir DIRECTORY",2,cwd
   for item in args:resolve_path(item,cwd,workspace).mkdir(parents=True,exist_ok=True)
   return "","",0,cwd
  if cmd=="touch":
   if not args:return "","usage: touch FILE",2,cwd
   for item in args:
    target=resolve_path(item,cwd,workspace)
    if not target.parent.is_dir():return "",f"touch: parent directory missing: {target.parent}",1,cwd
    target.touch(exist_ok=True)
   return "","",0,cwd
  if cmd in ("rm","del","erase"):
   if not args:return "","usage: rm FILE",2,cwd
   for item in args:
    target=resolve_path(item,cwd,workspace)
    if target.is_dir():return "","rm: directories are not removed in safe mode",1,cwd
    if target.exists():target.unlink()
   return "","",0,cwd
  if cmd in ("clear","cls","exit"):return "","",0,cwd
  return "",f"{cmd}: command is not available in safe mode; use --unsafe-shell only when you explicitly want local execution",127,cwd
 except (OSError,PermissionError,ValueError) as exc:return "",str(exc),1,cwd

def shell_command(shell:str,command:str):
 names={"bash":"bash","sh":"sh","zsh":"zsh","fish":"fish","cmd":"cmd.exe","powershell":"powershell.exe","chimera":"chimera"}
 exe=shutil.which(names.get(shell,""))
 if not exe:raise FileNotFoundError(f"selected shell is not installed: {shell}")
 if shell in ("bash","sh","zsh","fish"):return [exe,"-lc",command]
 if shell=="cmd":return [exe,"/d","/s","/c",command]
 if shell=="powershell":return [exe,"-NoLogo","-NoProfile","-Command",command]
 return [exe,"-c",command]

class BridgeServer(ThreadingHTTPServer):
 daemon_threads=True; allow_reuse_address=True
class Handler(BaseHTTPRequestHandler):
 server_version="AuroraLocalBridge/1.0"
 def log_message(self,fmt,*args):sys.stderr.write("[aurora-bridge] "+(fmt%args)+"\n")
 def origin_ok(self):
  origin=self.headers.get("Origin")
  if not origin:return True
  if origin==ALLOWED_ORIGIN:return True
  u=urlparse(origin);return u.scheme in ("http","https") and u.hostname in ("localhost","127.0.0.1")
 def cors(self):
  origin=self.headers.get("Origin")
  if origin and self.origin_ok():
   self.send_header("Access-Control-Allow-Origin",origin);self.send_header("Vary","Origin")
   self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
   self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type")
   self.send_header("Access-Control-Allow-Private-Network","true");self.send_header("Access-Control-Max-Age","600")
 def json(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode()
  self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
  self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store")
  self.cors();self.end_headers();self.wfile.write(raw)
 def authorized(self):
  supplied=self.headers.get("Authorization","")
  return supplied.startswith("Bearer ") and secrets.compare_digest(supplied[7:],self.server.token)
 def do_OPTIONS(self):
  if not self.origin_ok():return self.json(403,{"ok":False,"error":"origin is not allowed"})
  self.send_response(204);self.cors();self.end_headers()
 def do_GET(self):
  if not self.origin_ok():return self.json(403,{"ok":False,"error":"origin is not allowed"})
  if self.path=="/health":return self.json(200,{"ok":True,"mode":"unsafe-shell" if self.server.unsafe_shell else "safe","profile":self.server.profile})
  if self.path=="/api/capabilities":
   if not self.authorized():return self.json(401,{"ok":False,"error":"invalid or missing bearer token"})
   return self.json(200,{"ok":True,"mode":"unsafe-shell" if self.server.unsafe_shell else "safe","profile":self.server.profile,"workspace":str(self.server.workspace),"unsafe_shell":self.server.unsafe_shell,"shells":list(SHELLS),"commands":["pwd","cd","ls","cat","echo","whoami","hostname","uname","date","env","which","mkdir","touch","rm","clear","help"]})
  return self.json(404,{"ok":False,"error":"not found"})
 def do_POST(self):
  if not self.origin_ok():return self.json(403,{"ok":False,"error":"origin is not allowed"})
  if self.path!="/api/command":return self.json(404,{"ok":False,"error":"not found"})
  if not self.authorized():return self.json(401,{"ok":False,"error":"invalid or missing bearer token"})
  try:size=int(self.headers.get("Content-Length","0"))
  except ValueError:return self.json(400,{"ok":False,"error":"invalid content length"})
  if size<1 or size>MAX_BODY:return self.json(413,{"ok":False,"error":"request body size is invalid"})
  try:payload=json.loads(self.rfile.read(size))
  except (json.JSONDecodeError,UnicodeDecodeError):return self.json(400,{"ok":False,"error":"invalid JSON"})
  command=str(payload.get("command","")).strip()
  if not command or len(command)>MAX_COMMAND:return self.json(400,{"ok":False,"error":"command is empty or too long"})
  session=str(payload.get("session","default"))[:128];shell=str(payload.get("shell") or "bash").lower()
  if shell not in SHELLS:return self.json(400,{"ok":False,"error":"unsupported shell profile"})
  now=time.time();client=self.client_address[0]
  with LOCK:
   recent=[x for x in RATE.get(client,[]) if now-x<60]
   if len(recent)>=60:return self.json(429,{"ok":False,"error":"rate limit exceeded"})
   recent.append(now);RATE[client]=recent;cwd=SESSIONS.get(session,self.server.workspace)
  if self.server.unsafe_shell:
   try:
    argv=shell_command(shell,command);result=subprocess.run(argv,cwd=str(cwd),capture_output=True,text=True,timeout=30,check=False)
    out=(result.stdout or "")[:MAX_OUTPUT];err=(result.stderr or "")[:MAX_OUTPUT];code=result.returncode
   except (OSError,subprocess.TimeoutExpired,FileNotFoundError) as exc:out="";err=str(exc);code=124
   new_cwd=cwd
  else:out,err,code,new_cwd=safe_command(command,cwd,self.server.workspace,shell)
  with LOCK:SESSIONS[session]=new_cwd
  return self.json(200,{"ok":code==0,"output":out,"stderr":err,"exit_code":code,"mode":"unsafe-shell" if self.server.unsafe_shell else "safe","profile":self.server.profile,"cwd":str(new_cwd),"session":session})

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--workspace",type=Path,default=Path.home()/"ChimeraTerminalWorkspace")
 p.add_argument("--profile",choices=("chimera","octavian"),default="chimera")
 p.add_argument("--port",type=int,default=8767)
 p.add_argument("--unsafe-shell",action="store_true",help="allow explicitly selected local shells with current-user privileges")
 a=p.parse_args();workspace=a.workspace.expanduser().resolve();workspace.mkdir(parents=True,exist_ok=True)
 server=BridgeServer(("127.0.0.1",a.port),Handler)
 server.token=secrets.token_urlsafe(32);server.workspace=workspace;server.profile=a.profile;server.unsafe_shell=a.unsafe_shell
 print(f"Aurora local bridge: http://127.0.0.1:{a.port}",flush=True)
 print(f"Profile: {a.profile}; mode: {'UNSAFE FULL SHELL' if a.unsafe_shell else 'safe workspace'}",flush=True)
 print(f"Workspace: {workspace}",flush=True);print(f"One-time bearer token: {server.token}",flush=True)
 if a.unsafe_shell:print("WARNING: full host-shell execution is enabled for this local user.",file=sys.stderr,flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=="__main__":main()
