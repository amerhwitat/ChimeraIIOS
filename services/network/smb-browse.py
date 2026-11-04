#!/usr/bin/env python3
"""Explicit-target SMB share discovery using Samba's maintained SMB client tools."""
import argparse
import json
import re
import subprocess
import sys

HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,252}$")

def run(argv, timeout=25):
    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"}
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                       check=False, env=env)
    return p.returncode, p.stdout, p.stderr

def browse(host, kerberos=True):
    if not HOST.fullmatch(host):
        raise ValueError("host must be a DNS name or IPv4/IPv6 literal without URL syntax")
    argv = ["smbclient", "-g", "-L", "//" + host, "--option=client min protocol=SMB2"]
    if kerberos:
        argv.append("-k")
    else:
        raise ValueError("password/guest fallback is disabled; use a Kerberos ticket or explicit administrator tooling")
    code, out, err = run(argv)
    shares = []
    for line in out.splitlines():
        fields = line.split("|")
        if len(fields) >= 2 and fields[0].upper() == "DISK":
            shares.append({"name": fields[1], "comment": "|".join(fields[2:])})
    return {"host": host, "authenticated": True, "mechanism": "Kerberos credential cache",
            "returncode": code, "shares": shares,
            "error": err[-2000:] if code else None}

def browse_network():
    """Discover SMB services announced on the local link via DNS-SD/mDNS."""
    code, out, err = run(["avahi-browse", "-rt", "_smb._tcp"], timeout=35)
    servers = []
    for line in out.splitlines():
        if not line.startswith("="):
            continue
        fields = line.split(";")
        if len(fields) >= 9:
            servers.append({"interface": fields[1], "protocol": fields[2],
                            "name": fields[3], "domain": fields[5],
                            "host": fields[6], "address": fields[7],
                            "port": int(fields[8]) if fields[8].isdigit() else None})
    return {"discovery": "DNS-SD _smb._tcp", "returncode": code,
            "servers": servers, "error": err[-2000:] if code else None}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("host", nargs="?", help="explicit SMB server DNS name or IP")
    p.add_argument("--network", action="store_true", help="discover SMB services on the local link")
    p.add_argument("--no-kerberos", action="store_true", help=argparse.SUPPRESS)
    a = p.parse_args()
    try:
        if a.network:
            print(json.dumps(browse_network(), indent=2))
        elif a.host:
            print(json.dumps(browse(a.host, kerberos=not a.no_kerberos), indent=2))
        else:
            p.error("supply HOST or --network")
    except (ValueError, OSError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
