#!/usr/bin/env python3
import argparse,base64,hmac,json,os,pty,resource,shutil,signal,socket,struct,subprocess,termios,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ADAPTERS=ROOT/'system/terminal/shell_adapters.json'; PERMISSIONS=ROOT/'system/terminal/permissions.json'
LIMITS={'cpu_seconds':30,'address_space_bytes':1073741824,'file_size_bytes':134217728,'open_files':256,'processes':64}; SESSIONS={}
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def allowed(role,cap):
 c=load(PERMISSIONS).get('roles',{}).get(role,{}); return cap in c.get('allow',[]) and cap not in c.get('deny',[])
def auth(token,path):
 try: expected=Path(path).read_text(encoding='utf-8').strip()
 except OSError: return False
 return bool(expected) and hmac.compare_digest(token,expected)
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(LIMITS['cpu_seconds'],LIMITS['cpu_seconds'])); resource.setrlimit(resource.RLIMIT_AS,(LIMITS['address_space_bytes'],LIMITS['address_space_bytes'])); resource.setrlimit(resource.RLIMIT_FSIZE,(LIMITS['file_size_bytes'],LIMITS['file_size_bytes'])); resource.setrlimit(resource.RLIMIT_NOFILE,(LIMITS['open_files'],LIMITS['open_files']))
 if hasattr(resource,'RLIMIT_NPROC'): resource.setrlimit(resource.RLIMIT_NPROC,(LIMITS['processes'],LIMITS['processes']))
def shell_argv(name):
 c=load(ADAPTERS).get('adapters',{}).get(name)
 if not c or not isinstance(c.get('argv'),list): raise ValueError('unsupported shell adapter')
 return c['argv']
def backend():
 if shutil.which('bwrap'): return 'bwrap'
 if shutil.which('unshare') and os.geteuid()==0: return 'unshare'
 return None
def make_root(sid):
 root=Path(os.environ.get('CHIMERA_SANDBOX_ROOT','/var/lib/chimera/sandboxes'))/sid
 for d in ('home','tmp','data','work'): (root/d).mkdir(parents=True,exist_ok=True)
 import sqlite3
 db=root/'data'/'chimera.sqlite3'; con=sqlite3.connect(db); con.execute('PRAGMA journal_mode=WAL'); con.execute('PRAGMA foreign_keys=ON'); con.execute("CREATE TABLE IF NOT EXISTS chimera_session(key TEXT PRIMARY KEY,value TEXT NOT NULL)"); con.execute("INSERT OR REPLACE INTO chimera_session VALUES('format','1')"); con.commit(); con.close(); return root
def spawn(sid,shell,role,unsafe):
 if not allowed(role,'terminal.create'): raise PermissionError('terminal.create denied')
 b=backend()
 if not b and not unsafe: raise RuntimeError('no supported sandbox backend; refusing host execution')
 root=make_root(sid); master,slave=pty.openpty(); env=os.environ.copy(); env.update({'HOME':'/home','TMPDIR':'/tmp','TERM':'xterm-256color','CHIMERA_TERMINAL_SESSION':sid,'CHIMERA_TERMINAL_SANDBOX':str(root),'PATH':'/usr/local/bin:/usr/bin:/bin'}); cmd=shell_argv(shell)
 if b=='bwrap':
  cmd=['bwrap','--die-with-parent','--new-session','--proc','/proc','--dev','/dev','--ro-bind','/usr','/usr','--ro-bind','/bin','/bin','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--bind',str(root/'home'),'/home','--bind',str(root/'tmp'),'/tmp','--bind',str(root/'data'),'/data','--bind',str(root/'work'),'/work','--chdir','/work','--unshare-net']+cmd
  pre=lambda:(os.setsid(),limits())
 else:
  def pre():
   os.setsid(); limits(); os.chdir(root)
   if hasattr(os,'unshare'): os.unshare(os.CLONE_NEWNS|os.CLONE_NEWPID|os.CLONE_NEWNET)
 proc=subprocess.Popen(cmd,stdin=slave,stdout=slave,stderr=slave,env=env,close_fds=True,preexec_fn=pre); os.close(slave); os.set_blocking(master,False); return {'master':master,'pid':proc.pid,'root':root}
def send(c,o): c.sendall((json.dumps(o,separators=(',',':'))+'\n').encode())
def handle(c,cfg):
 line=c.makefile('rb').readline(1048576)
 if not line:return
 q=json.loads(line); token=str(q.get('token','')); role=str(q.get('role','terminal-user')); action=str(q.get('action','')); tf=cfg.get('authentication',{}).get('token_file','/etc/chimera/terminal/auth.token')
 if not auth(token,tf): send(c,{'ok':False,'error':'authentication failed'}); return
 if action=='create':
  sid=str(q.get('session') or ('t-'+str(os.getpid())+'-'+str(time.time_ns()))); unsafe=bool(q.get('unsafe_host')) and allowed(role,'terminal.host')
  try: s=spawn(sid,str(q.get('shell','bash')),role,unsafe); SESSIONS[sid]=s; send(c,{'ok':True,'session':sid,'pid':s['pid'],'sandbox':str(s['root']),'backend':backend() or 'unsafe-host'})
  except Exception as e: send(c,{'ok':False,'error':str(e)})
  return
 sid=str(q.get('session','')); s=SESSIONS.get(sid)
 if not s: send(c,{'ok':False,'error':'session not found'}); return
 if action=='write':
  if not allowed(role,'terminal.write'): send(c,{'ok':False,'error':'terminal.write denied'}); return
  os.write(s['master'],base64.b64decode(q.get('data',''))); send(c,{'ok':True})
 elif action=='read':
  if not allowed(role,'terminal.read'): send(c,{'ok':False,'error':'terminal.read denied'}); return
  try: data=os.read(s['master'],65536)
  except BlockingIOError: data=b''
  send(c,{'ok':True,'data':base64.b64encode(data).decode()})
 elif action=='resize':
  if not allowed(role,'terminal.resize'): send(c,{'ok':False,'error':'terminal.resize denied'}); return
  import fcntl; fcntl.ioctl(s['master'],termios.TIOCSWINSZ,struct.pack('HHHH',int(q.get('rows',24)),int(q.get('cols',80)),0,0)); send(c,{'ok':True})
 elif action=='close':
  try: os.killpg(s['pid'],signal.SIGHUP)
  except ProcessLookupError: pass
  SESSIONS.pop(sid,None); send(c,{'ok':True})
 else: send(c,{'ok':False,'error':'unknown action'})
def main():
 p=argparse.ArgumentParser(); p.add_argument('--socket',default='/run/chimera/terminald.sock'); p.add_argument('--config',default=str(ROOT/'system/terminal/terminal-service.json')); a=p.parse_args(); cfg=load(Path(a.config)); sock=Path(a.socket); sock.parent.mkdir(parents=True,exist_ok=True)
 try:sock.unlink()
 except FileNotFoundError:pass
 srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); srv.bind(sock); os.chmod(sock,0o660); srv.listen(64)
 while True:
  c,_=srv.accept()
  try: handle(c,cfg)
  except Exception as e:
   try: send(c,{'ok':False,'error':str(e)})
   except OSError: pass
  finally:c.close()
if __name__=='__main__': raise SystemExit(main())