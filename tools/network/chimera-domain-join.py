#!/usr/bin/env python3
"""Interactive Active Directory enrollment through realmd/adcli/SSSD."""
import argparse,re,shutil,subprocess,sys,os
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("domain");p.add_argument("--user",required=True);p.add_argument("--discover-only",action="store_true");a=p.parse_args()
 if os.geteuid()!=0:print("Run this enrollment helper as root; credentials are prompted by realmd.",file=sys.stderr);return 2
 if not re.fullmatch(r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*",a.domain):print("Invalid DNS domain name.",file=sys.stderr);return 2
 if not shutil.which("realm"):print("realm (realmd) is required",file=sys.stderr);return 2
 if subprocess.run(["realm","discover",a.domain],check=False).returncode:return 1
 if a.discover_only:return 0
 if not shutil.which("adcli") or not shutil.which("sssd"):print("adcli and sssd are required",file=sys.stderr);return 2
 print("Enrollment prompts interactively; this tool never accepts or stores a password.")
 if input("Join "+a.domain+" as "+a.user+"? Type JOIN: ")!="JOIN":print("Cancelled.");return 1
 return subprocess.run(["realm","join","--verbose","--user",a.user,a.domain],check=False).returncode
if __name__=="__main__":raise SystemExit(main())
