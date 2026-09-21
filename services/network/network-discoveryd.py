#!/usr/bin/env python3
"""Bounded discovery of administrator-configured private networks."""
import ipaddress,json,os,subprocess,time,pathlib
CFG=pathlib.Path(os.environ.get("CHIMERA_NETWORK_CONFIG","/etc/chimera/network-discovery.json"))
OUT=pathlib.Path(os.environ.get("CHIMERA_NETWORK_STATE","/var/lib/chimera/network"))
INTERVAL=int(os.environ.get("CHIMERA_NETWORK_INTERVAL","300"))
def load():
    if not CFG.exists(): return {"enabled":False,"networks":[]}
    try:return json.loads(CFG.read_text())
    except Exception:return {"enabled":False,"networks":[]}
def local_networks():
    try:
        p=subprocess.run(["ip","-4","route","show","scope","link"],capture_output=True,text=True,timeout=10)
        nets=[]
        for line in p.stdout.splitlines():
            first=line.split()[0] if line.split() else ""
            try:
                n=ipaddress.ip_network(first,strict=False)
                if n.is_private and n.prefixlen>=16 and n.prefixlen<=30: nets.append(str(n))
            except Exception: pass
        return sorted(set(nets))
    except Exception:return []

def scan(net):
    try:
        n=ipaddress.ip_network(net,strict=False)
        if not (n.is_private or n.is_loopback or n.is_link_local): return {"network":net,"error":"non-private scope rejected"}
        p=subprocess.run(["nmap","-sn","-oX","-",net],capture_output=True,text=True,timeout=120,check=False)
        return {"network":net,"returncode":p.returncode,"xml":p.stdout[-200000:]}
    except Exception as e:return {"network":net,"error":str(e)}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    while True:
        c=load()
        if c.get("enabled"):
            state={"timestamp":time.time(),"results":[scan(n) for n in c.get("networks",[])]}
            tmp=OUT/"discovery.json.tmp"; tmp.write_text(json.dumps(state,indent=2)); tmp.replace(OUT/"discovery.json")
        time.sleep(max(30,INTERVAL))
if __name__=="__main__": main()
