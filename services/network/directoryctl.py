#!/usr/bin/env python3
"""Active Directory and LDAP client integration through maintained system tools."""
import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit

DOMAIN = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$")
URI = re.compile(r"^(ldaps://|ldap://)[A-Za-z0-9.-]+(?::[0-9]{1,5})?/?$")

def valid_ldap_uri(value):
    if not URI.fullmatch(value):
        return False
    try:
        parsed = urlsplit(value)
        return bool(parsed.hostname) and (parsed.port is None or 1 <= parsed.port <= 65535) and parsed.path in ("", "/")
    except ValueError:
        return False
\ndef run(argv, timeout=90):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    join = sub.add_parser("join")
    join.add_argument("domain")
    join.add_argument("--user")
    status = sub.add_parser("status")
    ldap = sub.add_parser("ldap-search")
    ldap.add_argument("uri")
    ldap.add_argument("base_dn")
    ldap.add_argument("filter")
    ldap.add_argument("--limit", type=int, default=100)
    a = p.parse_args()
    try:
        if a.cmd == "join":
            if not DOMAIN.fullmatch(a.domain):
                raise ValueError("invalid AD DNS domain")
            argv = ["realm", "join", "--no-password", "--membership-software=adcli",
                    "--client-software=sssd", a.domain]
            if a.user:
                if not re.fullmatch(r"[A-Za-z0-9._@-]{1,128}", a.user):
                    raise ValueError("invalid directory account name")
                argv += ["--user=" + a.user]
            result = run(argv, timeout=180)
        elif a.cmd == "status":
            result = run(["realm", "list"], timeout=15)
        else:
            if (not valid_ldap_uri(a.uri) or not a.base_dn or "\n" in a.base_dn or
                    not re.fullmatch(r"[A-Za-z0-9=,._ -]{1,512}", a.base_dn) or
                    not a.filter.startswith("(") or len(a.filter) > 4096 or "\n" in a.filter):
                raise ValueError("LDAP URI must be ldap(s)://host[:port]; base DN is required")
            if a.uri.startswith("ldap://"):
                argv = ["ldapsearch", "-LLL", "-ZZ", "-o", "TLS_REQCERT=demand",
                        "-Y", "GSSAPI", "-H", a.uri, "-b", a.base_dn,
                        "-z", str(max(1, min(a.limit, 1000))), a.filter]
            else:
                argv = ["ldapsearch", "-LLL", "-o", "TLS_REQCERT=demand",
                        "-Y", "GSSAPI", "-H", a.uri, "-b", a.base_dn,
                        "-z", str(max(1, min(a.limit, 1000))), a.filter]
            result = run(argv, timeout=45)
        print(json.dumps({"returncode": result.returncode, "stdout": result.stdout[-20000:],
                          "stderr": result.stderr[-4000:]}, indent=2))
        return result.returncode
    except (ValueError, OSError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
