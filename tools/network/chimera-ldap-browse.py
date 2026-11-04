#!/usr/bin/env python3
"""Safe LDAP directory browsing using StartTLS/LDAPS and optional Kerberos GSSAPI."""
import argparse,shutil,subprocess,sys
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--server",required=True,help="ldap://host or ldaps://host")
 p.add_argument("--base",required=True);p.add_argument("--filter",default="(objectClass=*)")
 p.add_argument("--scope",choices=("base","one","sub"),default="sub")
 p.add_argument("--ldaps",action="store_true");p.add_argument("--kerberos",action="store_true")
 a=p.parse_args()
 if not shutil.which("ldapsearch"):print("ldapsearch is required (OpenLDAP client tools)",file=sys.stderr);return 2
 if not a.server.startswith(("ldap://","ldaps://")):print("Server must use ldap:// or ldaps://",file=sys.stderr);return 2
 if a.server.startswith("ldap://") and a.ldaps:print("Use an ldaps:// URL for LDAPS",file=sys.stderr);return 2
 cmd=["ldapsearch","-LLL","-H",a.server,"-b",a.base,"-s",a.scope]
 if a.server.startswith("ldap://"):cmd.append("-ZZ")
 if a.kerberos:cmd += ["-Y","GSSAPI"]
 cmd.append(a.filter)
 return subprocess.run(cmd,check=False).returncode
if __name__=="__main__":raise SystemExit(main())
