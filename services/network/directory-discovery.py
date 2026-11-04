#!/usr/bin/env python3
"""AD domain-controller discovery through DNS SRV; no domain join side effects."""
import argparse,json,re,shutil,subprocess,sys
DOMAIN=re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$")
def discover(domain):
 if not DOMAIN.fullmatch(domain):raise ValueError("invalid DNS domain")
 if not shutil.which("dig"):raise RuntimeError("dig from dnsutils is required")
 results={}
 for name in ("_ldap._tcp.dc._msdcs."+domain,"_kerberos._tcp."+domain,"_kerberos._udp."+domain,"_kpasswd._tcp."+domain):
  p=subprocess.run(["dig","+time=3","+tries=1","+short","SRV",name],capture_output=True,text=True,timeout=5);rows=[]
  for line in p.stdout.splitlines():
   f=line.split()
   if len(f)==4 and all(x.isdigit() for x in f[:3]):
    port=int(f[2])
    if 1<=port<=65535:rows.append({"priority":int(f[0]),"weight":int(f[1]),"port":port,"target":f[3].rstrip(".")})
  results[name]=rows
 return {"domain":domain,"records":results,"domain_controllers":results["_ldap._tcp.dc._msdcs."+domain]}
def main():
 p=argparse.ArgumentParser();p.add_argument("domain");a=p.parse_args()
 try:print(json.dumps(discover(a.domain),indent=2));return 0
 except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as e:print(json.dumps({"error":str(e)}),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
