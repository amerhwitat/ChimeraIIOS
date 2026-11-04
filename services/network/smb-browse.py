#!/usr/bin/env python3
"""Explicit-target SMB share discovery using Samba's maintained SMB client tools."""
import argparse
import json
import re
import subprocess
import sys
import socket
import os
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "registry"))
from registry_client import get_value

HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,252}$")

def run(argv, timeout=25):
    env = os.environ.copy()
    env.update({"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                       check=False, env=env)
    return p.returncode, p.stdout, p.stderr

def smb_client_settings():
    minimum = get_value("machine", "machine.network.smb.minimum_protocol", "SMB2_10")
    if minimum not in ("SMB2_10", "SMB3_00", "SMB3_02", "SMB3_11"):
        raise ValueError("registry SMB minimum protocol is outside the safe SMB2/3 allowlist")
    workgroup = get_value("environment", "environment.network.workgroup", "WORKGROUP")
    if not isinstance(workgroup, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,15}", workgroup):
        raise ValueError("invalid configured SMB workgroup")
    return minimum, workgroup

def browse(host, kerberos=True):
    if not HOST.fullmatch(host):
        raise ValueError("host must be a DNS name or IPv4 address without URL syntax")
    minimum, workgroup = smb_client_settings()
    argv = ["smbclient", "-g", "-L", "//" + host,
            "--option=client min protocol=" + minimum, "--option=client signing=mandatory",
            "-W", workgroup]
    if kerberos:
        argv.append("--use-kerberos=required")
    else:
        raise ValueError("password/guest fallback is disabled; use a Kerberos ticket or explicit administrator tooling")
    code, out, err = run(argv)
    shares = []
    for line in out.splitlines():
        fields = line.split("|")
        if len(fields) >= 2 and fields[0].upper() == "DISK":
            shares.append({"name": fields[1], "comment": "|".join(fields[2:])})
    return {"host": host, "authenticated": code == 0, "mechanism": "Kerberos credential cache",
            "returncode": code, "shares": shares,
            "error": err[-2000:] if code else None}

def ws_discover(timeout=3.0):
    """Send a bounded WS-Discovery Probe on the local link; never scan IP ranges."""
    message_id = "urn:uuid:" + str(uuid.uuid4())
    envelope = ('''<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:a="http://www.w3.org/2005/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:dp="http://schemas.xmlsoap.org/ws/2006/02/devprof">
 <s:Header>
  <a:MessageID>''' + message_id + '''</a:MessageID>
  <a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>
  <a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>
 </s:Header>
 <s:Body><d:Probe><d:Types>dp:Device</d:Types></d:Probe></s:Body>
</s:Envelope>''').encode("utf-8")
    found = {}
    deadline = time.monotonic() + max(0.5, min(timeout, 5.0))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        sock.settimeout(0.25)
        sock.sendto(envelope, ("239.255.255.250", 3702))
        while time.monotonic() < deadline:
            try:
                packet, peer = sock.recvfrom(65535)
            except socket.timeout:
                continue
            try:
                root = ET.fromstring(packet)
                addresses = [node.text for node in root.iter()
                             if node.tag.endswith("}XAddrs") and node.text]
                endpoint = next((node.text for node in root.iter()
                                 if node.tag.endswith("}Address") and node.text), "")
                found[peer[0]] = {"address": peer[0], "endpoint": endpoint,
                                  "xaddrs": addresses, "discovery": "WS-Discovery"}
            except ET.ParseError:
                continue
    return list(found.values())

def browse_network():
    """Discover SMB services announced on the local link via DNS-SD/mDNS."""
    try:
        code, out, err = run(["avahi-browse", "-rt", "_smb._tcp"], timeout=35)
    except OSError as exc:
        code, out, err = 1, "", str(exc)
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
    try:
        wsd_servers = ws_discover()
    except OSError as exc:
        wsd_servers = []
        err = (err + " " + str(exc)).strip()
    merged = {item["address"]: item for item in wsd_servers}
    for item in servers:
        merged[item["address"]] = item
    return {"discovery": ["DNS-SD _smb._tcp", "WS-Discovery Probe"],
            "returncode": code, "servers": list(merged.values()),
            "error": err[-2000:] if code or err else None}

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
