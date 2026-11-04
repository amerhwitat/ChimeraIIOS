#!/usr/bin/env python3
"""Active Directory and LDAP client integration through maintained system tools."""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "registry"))
from registry_client import get_value

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

def run(argv, timeout=90):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    join = sub.add_parser("join")
    join.add_argument("domain", nargs="?")
    join.add_argument("--user")
    join.add_argument("--elevate", action="store_true", help="use PolicyKit after validating the current user's Kerberos ticket cache")
    status = sub.add_parser("status")
    ldap = sub.add_parser("ldap-search")
    ldap.add_argument("uri")
    ldap.add_argument("base_dn")
    ldap.add_argument("filter")
    ldap.add_argument("--limit", type=int, default=100)
    a = p.parse_args()
    try:
        if a.cmd == "join":
            domain = a.domain or get_value("environment", "environment.directory.preferred_domain", "")
            if not isinstance(domain, str) or not DOMAIN.fullmatch(domain):
                raise ValueError("supply a valid AD DNS domain or set environment.directory.preferred_domain")
            argv = ["realm", "join", "--no-password", "--membership-software=adcli",
                    "--client-software=sssd", domain]
            if a.user:
                if not re.fullmatch(r"[A-Za-z0-9._@-]{1,128}", a.user):
                    raise ValueError("invalid directory account name")
                argv.insert(-1, "--user=" + a.user)
            if a.elevate:
                cache = os.environ.get("KRB5CCNAME", "FILE:/tmp/krb5cc_%d" % os.getuid())
                if not cache.startswith("FILE:"):
                    raise ValueError("elevated domain join requires a FILE: Kerberos ticket cache")
                cache_path = Path(cache[5:])
                if not cache_path.is_absolute() or "\n" in str(cache_path):
                    raise ValueError("Kerberos ticket cache path must be absolute and single-line")
                try:
                    st = cache_path.lstat()
                except OSError as exc:
                    raise ValueError("Kerberos ticket cache is unavailable; run kinit first") from exc
                if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or
                        stat.S_IMODE(st.st_mode) & 0o077):
                    raise ValueError("Kerberos ticket cache must be a private regular file owned by this user")
                ticket = run(["klist", "-s"], timeout=10)
                if ticket.returncode:
                    raise ValueError("no valid Kerberos ticket; run kinit before joining the domain")
                pkexec = shutil.which("pkexec")
                if not pkexec:
                    raise RuntimeError("pkexec/PolicyKit is required for an administrator-approved domain join")
                realm = shutil.which("realm") or "/usr/sbin/realm"
                argv = [pkexec, "/usr/bin/env", "KRB5CCNAME=FILE:" + str(cache_path), realm] + argv[1:]
            result = run(argv, timeout=180)
        elif a.cmd == "status":
            result = run(["realm", "list"], timeout=15)
        else:
            if (not valid_ldap_uri(a.uri) or not a.base_dn or "\n" in a.base_dn or
                    not re.fullmatch(r"[A-Za-z0-9=,._ -]{1,512}", a.base_dn) or
                    not a.filter.startswith("(") or not a.filter.endswith(")") or len(a.filter) > 4096 or "\n" in a.filter or "\0" in a.filter):
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
