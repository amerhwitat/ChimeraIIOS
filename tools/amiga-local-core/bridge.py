#!/usr/bin/env python3
import json, os, shutil, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
CORE=os.path.join(ROOT,'.local','amiga-core','cores','puae_libretro.so')
HOST='127.0.0.1'; PORT=8765

def send(h,code,payload):
    raw=json.dumps(payload).encode()
    h.send_response(code); h.send_header('Content-Type','application/json')
    h.send_header('Access-Control-Allow-Origin','*'); h.send_header('Access-Control-Allow-Headers','Content-Type')
    h.end_headers(); h.wfile.write(raw)

class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self): send(self,204,{})
    def do_GET(self):
        if self.path=='/health':
            send(self,200,{'ok':True,'version':'chimera-amiga-local-bridge/1','core':os.path.exists(CORE)})
        else: send(self,404,{'error':'not-found'})
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0')); data=json.loads(self.rfile.read(n) or b'{}')
        if self.path=='/launch/amiga':
            if not os.path.exists(CORE): return send(self,409,{'error':'local PUAE core not built','build':'tools/amiga-local-core/build-local-core.sh'})
            content=os.path.realpath(os.path.expanduser(str(data.get('content','')).strip()))
            if not content: return send(self,400,{'error':'content path required'})
            if not os.path.isfile(content): return send(self,404,{'error':'content file not found'})
            allowed={'.adf','.adz','.dms','.fdi','.ipf','.hdf','.hdz','.lha','.zip','.m3u','.iso','.cue','.chd'}
            if os.path.splitext(content)[1].lower() not in allowed: return send(self,415,{'error':'unsupported Amiga content format'})
            retro=shutil.which('retroarch')
            if not retro: return send(self,409,{'error':'retroarch not installed'})
            cmd=[retro,'-L',CORE,content]
            subprocess.Popen(cmd,start_new_session=True)
            return send(self,200,{'ok':True,'command':cmd})
        if self.path=='/launch/commodore':
            model=str(data.get('model','c64')).strip().lower()
            providers={
                'c64':('x64sc',{'.d64','.g64','.crt','.prg','.t64','.tap','.zip'}),
                'c128':('x128',{'.d64','.d71','.d81','.prg','.t64','.tap','.crt','.zip'}),
                'vic20':('xvic',{'.d64','.prg','.crt','.tap','.zip'}),
                'plus4':('xplus4',{'.d64','.prg','.crt','.tap','.zip'}),
                'pet':('xpet',{'.d64','.prg','.crt','.zip'})
            }
            if model not in providers: return send(self,400,{'error':'unsupported Commodore model','supported':sorted(providers)})
            binary,extensions=providers[model]
            emulator=shutil.which(binary)
            if not emulator: return send(self,409,{'error':'VICE emulator not installed','provider':binary})
            content=os.path.realpath(os.path.expanduser(str(data.get('content','')).strip()))
            if not content: return send(self,400,{'error':'content path required'})
            if not os.path.isfile(content): return send(self,404,{'error':'content file not found'})
            if os.path.splitext(content)[1].lower() not in extensions: return send(self,415,{'error':'unsupported disk/program format','supported':sorted(extensions)})
            command=[emulator,'-autostart',content]
            subprocess.Popen(command,start_new_session=True)
            return send(self,200,{'ok':True,'model':model,'provider':binary,'command':command})
        if self.path=='/launch/mame':
            retro=shutil.which('mame') or shutil.which('mame64')
            if not retro: return send(self,409,{'error':'MAME executable not found locally'})
            command=str(data.get('command','')).strip()
            if not command.startswith('mame '): return send(self,400,{'error':'invalid MAME command'})
            args=command.split()[1:]
            subprocess.Popen([retro,*args],start_new_session=True)
            return send(self,200,{'ok':True})
        if self.path=='/mame/validate':
            retro=shutil.which('mame') or shutil.which('mame64')
            if not retro: return send(self,409,{'error':'MAME executable not found locally'})
            machine=str(data.get('machine','')).strip()
            if not machine:return send(self,400,{'error':'machine required'})
            p=subprocess.run([retro,machine,'-verifyroms'],capture_output=True,text=True,timeout=60)
            return send(self,200,{'ok':p.returncode==0,'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-4000:]})
        send(self,404,{'error':'not-found'})
    def log_message(self,fmt,*args): print(fmt%args)

if __name__=='__main__':
    print(f'Chimera local emulator bridge listening on http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
