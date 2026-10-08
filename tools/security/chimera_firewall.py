#!/usr/bin/env python3
import argparse,json,shutil,subprocess
from pathlib import Path
POLICY=Path("/etc/chimera/firewall-policy.json")
def load(p=POLICY): return json.loads(Path(p).read_text())
def render(profile,policy):
    p=policy["profiles"][profile]
    lines=["table inet chimera {"," chain input { type filter hook input priority 0; policy %s;"%p["default_input"],"  iif lo accept","  ct state established,related accept","  ct state invalid drop"]
    if p.get("allow_icmp"): lines += ["  ip protocol icmp accept","  ip6 nexthdr icmpv6 accept"]
    if p.get("allow_mdns"): lines += ["  udp dport 5353 accept"]
    if p.get("allow_dns"): lines += ["  udp dport 53 accept","  tcp dport 53 accept"]
    if p.get("allow_kerberos"): lines += ["  udp dport 88 accept","  tcp dport 88 accept","  tcp dport 464 accept","  udp dport 464 accept"]
    lines += [" }"," chain output { type filter hook output priority 0; policy %s; }"%p["default_output"]," chain forward { type filter hook forward priority 0; policy %s; }"%p["default_forward"],"}"]
    return "\n".join(lines)+"\n"
def apply(profile,policy_path=str(POLICY)):
    if not shutil.which("nft"): raise RuntimeError("nft not installed")
    rules=render(profile,load(policy_path))
    subprocess.run(["nft","-f","-"],input=rules,text=True,check=True)
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("profile",choices=["private","public","wide-area","domain"]); ap.add_argument("--policy",default=str(POLICY)); ap.add_argument("--print",action="store_true")
    a=ap.parse_args(); rules=render(a.profile,load(a.policy))
    if a.print: print(rules)
    else: apply(a.profile,a.policy)
