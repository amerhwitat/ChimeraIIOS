#!/usr/bin/env python3
"""Authenticated loopback bridge for Aurora Terminal. Safe commands by default."""
from __future__ import annotations
import argparse, getpass, hmac, ipaddress, json, os, platform, secrets, shlex, shutil, socket, subprocess, sys, threading, time
from collections import deque
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

MAX_BODY=16384
MAX_OUTPUT=24000
MAX_FILE=1024*1024
SAFE={"help","clear","exit","pwd","cd","ls","dir","cat","type","head","tail","wc","grep","echo","printf","whoami","hostname","uname","date","id","env","which","command","history","mkdir","touch","rm","rmdir","tree","git"}

class TerminalService:
    def __init__(self,workspace,unsafe_shell=False):
        self.workspace=Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True,exist_ok=True)
        self.unsafe_shell=unsafe_shell
        self.sessions={}
        self.lock=threading.Lock()
    def _session(self,sid):
        if not isinstance(sid,str) or not sid or len(sid)>80 or not all(c.isalnum() or c in "._-" for c in sid):
            sid=secrets.token_urlsafe(18)
        with self.lock:
            if sid not in self.sessions:self.sessions[sid]={"cwd":self.workspace,"history":[],"requests":deque()}
            return sid,self.sessions[sid]
    def _path(self,session,value="."):
        p=Path(value or ".")
        if not p.is_absolute():p=session["cwd"]/p
        p=p.resolve()
        try:p.relative_to(self.workspace)
        except ValueError:raise ValueError("Path is outside the configured terminal workspace")
        return p
    def execute(self,payload):
        raw=str(payload.get("command","")).strip()
        shell=str(payload.get("shell","bash")).lower()
        if shell not in {"bash","zsh","fish","pwsh","powershell","cmd","nu","chimera"}:raise ValueError("Unsupported shell profile")
        if not raw:return {"ok":True,"output":"","cwd":str(self.workspace),"mode":"safe"}
        if len(raw)>4096 or chr(0) in raw:raise ValueError("Command is too long or contains invalid characters")
        sid,s=self._session(payload.get("session"))
        now=time.monotonic()
        while s["requests"] and now-s["requests"][0]>60:s["requests"].popleft()
        if len(s["requests"])>=40:raise ValueError("Rate limit reached")
        s["requests"].append(now)
        s["history"].append(raw);s["history"]=s["history"][-100:]
        if self.unsafe_shell:out,code=self._shell(raw,shell,s);mode="local-shell"
        else:out,code=self._safe(raw,shell,s);mode="safe"
        return {"ok":True,"output":out[:MAX_OUTPUT],"exit_code":code,"cwd":str(s["cwd"]),"session":sid,"shell":shell,"mode":mode}
    def _safe(self,raw,shell,s):
        if any(x in raw for x in ("|",";","&",">","<",chr(96),"$","\n","\r")):
            raise ValueError("Pipes, redirection, chaining and substitutions are disabled in safe mode")
        try:parts=shlex.split(raw)
        except ValueError as e:raise ValueError(f"Parse error: {e}")
        if not parts:return "",0
        cmd,args=parts[0].lower(),parts[1:]
        aliases={
          "cmd":{"cls":"clear","ver":"uname","type":"cat","dir":"ls"},
          "pwsh":{"get-location":"pwd","set-location":"cd","get-childitem":"ls","get-content":"cat","write-output":"echo","write-host":"echo","get-date":"date","get-command":"which","clear-host":"clear"},
          "powershell":{"get-location":"pwd","set-location":"cd","get-childitem":"ls","get-content":"cat","write-output":"echo","write-host":"echo","get-date":"date","get-command":"which","clear-host":"clear"}}
        cmd=aliases.get(shell,{}).get(cmd,cmd)
        if cmd not in SAFE:raise ValueError(f"{cmd}: not enabled in safe browser-terminal mode")
        if cmd=="help":return "Safe commands: "+", ".join(sorted(SAFE)),0
        if cmd=="clear":return "",0
        if cmd=="exit":return "Session closed",0
        if cmd=="pwd":return str(s["cwd"]),0
        if cmd=="cd":
            p=self._path(s,args[0] if args else str(self.workspace))
            if not p.is_dir():raise ValueError("cd: not a directory")
            s["cwd"]=p;return "",0
        if cmd in {"ls","dir"}:
            p=self._path(s,next((x for x in reversed(args) if not x.startswith("-")),"."))
            if not p.is_dir():raise ValueError("ls: not a directory")
            items=sorted(x.name+("/" if x.is_dir() else "") for x in p.iterdir() if "-a" in args or not x.name.startswith("."))
            return "\n".join(items) if items else "(empty)",0
        if cmd in {"cat","type","head","tail","wc","grep"}:
            if not args:raise ValueError(f"usage: {cmd} FILE")
            if cmd=="grep":
                if len(args)<2:raise ValueError("usage: grep PATTERN FILE")
                pattern=args[0];p=self._path(s,args[-1])
            else:p=self._path(s,args[-1])
            if not p.is_file():raise ValueError("not a regular file")
            if p.stat().st_size>MAX_FILE:raise ValueError("file exceeds safe read limit")
            text=p.read_text(encoding="utf-8",errors="replace");lines=text.splitlines()
            if cmd in {"cat","type"}:return text,0
            if cmd=="head" or cmd=="tail":
                n=10
                if "-n" in args:
                    try:n=max(0,min(500,int(args[args.index("-n")+1])))
                    except Exception:raise ValueError("invalid line count")
                return "\n".join(lines[:n] if cmd=="head" else lines[-n:]),0
            if cmd=="wc":return f"{len(lines)} {len(text.split())} {len(text)} {p.name}",0
            return "\n".join(x for x in lines if pattern in x),0
        if cmd in {"echo","printf"}:return " ".join(args),0
        if cmd=="whoami":return getpass.getuser(),0
        if cmd=="hostname":return socket.gethostname(),0
        if cmd=="uname":return platform.platform(),0
        if cmd=="date":return datetime.now().astimezone().isoformat(),0
        if cmd=="id":return (f"uid={os.getuid()} gid={os.getgid()}" if hasattr(os,"getuid") else getpass.getuser()),0
        if cmd=="env":
            keys=("USER","USERNAME","HOME","SHELL","LANG","TERM","OS")
            return "\n".join(f"{k}={os.environ[k]}" for k in keys if k in os.environ),0
        if cmd in {"which","command"}:
            name=args[-1] if args else "";return (f"builtin:{name}" if name in SAFE else f"{name}: not found"),0
        if cmd=="history":return "\n".join(f"{i+1}  {v}" for i,v in enumerate(s["history"])),0
        if cmd in {"mkdir","touch","rm","rmdir"}:
            if not args:raise ValueError(f"usage: {cmd} PATH")
            p=self._path(s,args[-1])
            if p==self.workspace:raise ValueError("refusing to mutate workspace root")
            if cmd=="mkdir":p.mkdir(parents="-p" in args,exist_ok="-p" in args);return "",0
            if cmd=="touch":p.parent.mkdir(parents=True,exist_ok=True);p.touch(exist_ok=True);return "",0
            if cmd=="rm":
                if not p.is_file():raise ValueError("rm only removes regular files in safe mode")
                p.unlink();return "",0
            if not p.is_dir():raise ValueError("rmdir requires an empty directory")
            p.rmdir();return "",0
        if cmd=="tree":
            root=self._path(s,args[0] if args else ".")
            if not root.is_dir():raise ValueError("tree: not a directory")
            out=[];count=0
            for current,dirs,files in os.walk(root):
                depth=len(Path(current).relative_to(root).parts)
                if depth>=3:dirs[:]=[]
                for name in sorted(dirs+files):
                    out.append("  "*depth+name+("/" if (Path(current)/name).is_dir() else ""));count+=1
                    if count>=200:out.append("... truncated ...");return "\n".join(out),0
            return "\n".join(out) if out else "(empty)",0
        if cmd=="git":
            if not args or args[0] not in {"status","log","branch"}:raise ValueError("safe git supports status, log and branch")
            if not (self.workspace/".git").exists():return "not a git repository (safe workspace)",1
            call=["git",args[0]]
            if args[0]=="log":call+=["--oneline","-10"]
            r=subprocess.run(call,cwd=s["cwd"],capture_output=True,text=True,timeout=3,check=False)
            return r.stdout+r.stderr,r.returncode
        raise ValueError(f"{cmd}: not implemented")
    def _shell(self,raw,shell,s):
        if raw.lower().startswith("cd ") and not any(x in raw for x in (";","|","&",">","<",chr(96),"$")):
            try:
                p=self._path(s,shlex.split(raw)[1])
                if not p.is_dir():return "cd: not a directory",1
                s["cwd"]=p;return "",0
            except Exception as e:return str(e),1
        if shell in {"bash","zsh","fish","nu","chimera"}:
            exe="bash" if shell=="chimera" else shell;args=[exe,"-lc",raw] if exe in {"bash","zsh","fish"} else [exe,"-c",raw]
        elif shell in {"pwsh","powershell"}:exe="pwsh";args=[exe,"-NoLogo","-NoProfile","-NonInteractive","-Command",raw]
        elif shell=="cmd":
            if os.name!="nt":return "cmd.exe is only available on Windows hosts",69
            exe="cmd.exe";args=[exe,"/d","/s","/c",raw]
        else:return "unsupported shell",69
        if not shutil.which(exe):return f"{exe} is not installed on this host",69
        env={k:v for k,v in os.environ.items() if k in {"PATH","HOME","USER","USERNAME","LANG","LC_ALL","TERM","TMPDIR","TEMP","SYSTEMROOT","WINDIR","USERPROFILE","PATHEXT","APPDATA"}}
        try:
            r=subprocess.run(args,cwd=s["cwd"],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace",timeout=15,check=False)
            return r.stdout,r.returncode
        except subprocess.TimeoutExpired as e:return (e.stdout or "")+"\nCommand timed out after 15 seconds",124

ORIGINS={"https://amerhwitat.github.io","http://localhost:5500","http://127.0.0.1:5500","http://localhost:8000","http://127.0.0.1:8000"}
class Handler(BaseHTTPRequestHandler):
    server_version="ChimeraTerminalBridge/1.0"
    def log_message(self,fmt,*args):sys.stderr.write("terminal-bridge: "+fmt%args+"\n")
    def _host_ok(self):return self.headers.get("Host","") in self.server.allowed_hosts
    def _origin_ok(self):
        origin=self.headers.get("Origin");return not origin or origin in self.server.allowed_origins
    def _json(self,status,obj):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store")
        origin=self.headers.get("Origin")
        if origin and origin in self.server.allowed_origins:self.send_header("Access-Control-Allow-Origin",origin);self.send_header("Vary","Origin")
        self.end_headers();self.wfile.write(body)
    def _auth(self):
        h=self.headers.get("Authorization","")
        return h.startswith("Bearer ") and hmac.compare_digest(h[7:],self.server.token)
    def do_OPTIONS(self):
        if not self._host_ok() or not self._origin_ok():return self._json(403,{"ok":False,"error":"origin-or-host-denied"})
        self.send_response(204);origin=self.headers.get("Origin")
        if origin:self.send_header("Access-Control-Allow-Origin",origin)
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age","600");self.send_header("Vary","Origin");self.end_headers()
    def do_GET(self):
        if not self._host_ok() or not self._origin_ok():return self._json(403,{"ok":False,"error":"origin-or-host-denied"})
        path=urlparse(self.path).path
        if path=="/health":return self._json(200,{"ok":True,"service":"chimera-terminal-bridge","mode":"unsafe-shell-enabled" if self.server.service.unsafe_shell else "safe-commands-only"})
        if path=="/api/capabilities":
            if not self._auth():return self._json(401,{"ok":False,"error":"bearer-token-required"})
            return self._json(200,{"ok":True,"mode":"unsafe-shell-enabled" if self.server.service.unsafe_shell else "safe-commands-only","unsafe_shell":self.server.service.unsafe_shell,"workspace":str(self.server.service.workspace),"commands":sorted(SAFE)})
        return self._json(404,{"ok":False,"error":"not-found"})
    def do_POST(self):
        if not self._host_ok() or not self._origin_ok():return self._json(403,{"ok":False,"error":"origin-or-host-denied"})
        if urlparse(self.path).path!="/api/command":return self._json(404,{"ok":False,"error":"not-found"})
        if not self._auth():return self._json(401,{"ok":False,"error":"bearer-token-required"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n<1 or n>MAX_BODY:raise ValueError("invalid request size")
            payload=json.loads(self.rfile.read(n))
            if not isinstance(payload,dict):raise ValueError("JSON body must be an object")
            return self._json(200,self.server.service.execute(payload))
        except (ValueError,json.JSONDecodeError) as e:return self._json(400,{"ok":False,"error":str(e)})
        except Exception as e:return self._json(500,{"ok":False,"error":str(e)})

class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,address,service,token,origins):
        super().__init__(address,Handler);self.service=service;self.token=token
        self.allowed_origins=set(origins)
        self.allowed_hosts={f"{address[0]}:{address[1]}",f"localhost:{address[1]}",f"127.0.0.1:{address[1]}"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=8767)
    p.add_argument("--workspace",type=Path,default=Path.home()/"ChimeraWebTerminal")
    p.add_argument("--token",default=os.environ.get("CHIMERA_TERMINAL_TOKEN"))
    p.add_argument("--unsafe-shell",action="store_true",help="allow full local shell commands as the current user")
    p.add_argument("--allow-origin",action="append",default=[])
    a=p.parse_args()
    try:
        if not ipaddress.ip_address(a.host).is_loopback:p.error("host must be loopback")
    except ValueError:p.error("host must be a loopback IP address")
    if a.port<1 or a.port>65535:p.error("port must be 1..65535")
    token=a.token or secrets.token_urlsafe(32)
    service=TerminalService(a.workspace,a.unsafe_shell)
    server=Server((a.host,a.port),service,token,ORIGINS|set(a.allow_origin))
    print(f"Listening: http://{a.host}:{a.port}",file=sys.stderr)
    print(f"Bearer token (paste into Aurora Terminal): {token}",file=sys.stderr)
    print(f"Workspace: {service.workspace}",file=sys.stderr)
    print("Mode: REAL LOCAL SHELL ENABLED" if a.unsafe_shell else "Mode: SAFE WORKSPACE COMMANDS ONLY",file=sys.stderr)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=="__main__":raise SystemExit(main())
