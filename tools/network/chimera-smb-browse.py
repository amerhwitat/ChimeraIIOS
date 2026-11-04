#!/usr/bin/env python3
"""SMB network discovery and share enumeration using maintained Samba tools."""
import argparse,json,re,shutil,subprocess,sys
def run(argv,timeout=25):
 return subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
def discover():
 if not shutil.which("avahi-browse"): raise RuntimeError("avahi-browse is not installed; install Avahi for DNS-SD discovery")
 p=run(["avahi-browse","-rt","_smb._tcp"],35)
 if p.returncode not in (0,1): raise RuntimeError(p.stderr.strip() or "Avahi discovery failed")
 hosts={}
 for line in p.stdout.splitlines():
  if not line.startswith("="): continue
  f=line.split(";")
  if len(f)>=9:
   name,host,port=f[3],f[6],f[7]
   if host and port.isdigit(): hosts[host]={"name":name,"host":host,"port":int(port)}
 return list(hosts.values())
def shares(host,user=None,kerberos=False):
 if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]{0,252}",host): raise ValueError("invalid SMB host name")
 if not user and not kerberos: raise ValueError("authenticate with --user or --kerberos; anonymous access is disabled")
 if not shutil.which("smbclient"): raise RuntimeError("smbclient is not installed")
 cmd=["smbclient","-g","-L","//"+host]
 if kerberos: cmd += ["--use-kerberos=required"]
 elif user: cmd += ["-U",user]

 p=run(cmd,35)
 if p.returncode: raise RuntimeError(p.stderr.strip() or "SMB share enumeration failed")
 result=[]
 for line in p.stdout.splitlines():
  f=line.split("|")
  if len(f)>=2 and f[0] in ("Disk","IPC","Printer"): result.append({"kind":f[0],"name":f[1],"comment":f[2] if len(f)>2 else ""})
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--discover",action="store_true");p.add_argument("--host");p.add_argument("--user");p.add_argument("--kerberos",action="store_true");a=p.parse_args()
 try:
  if a.discover: print(json.dumps(discover(),indent=2))
  elif a.host: print(json.dumps({"host":a.host,"shares":shares(a.host,a.user,a.kerberos)},indent=2))
  else:p.error("choose --discover or --host")
  return 0
 except Exception as e:print("chimera-smb-browse: "+str(e),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
