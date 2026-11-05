#!/usr/bin/env python3
"""Safe Cisco IOS/Junos command adapter for Chimera Spotnik/FRR."""
from __future__ import annotations
import argparse, ipaddress, json, os, platform, re, shlex, shutil, subprocess, sys
from dataclasses import asdict, dataclass
CONFIRM = "APPLY-ROUTING-CHANGES"
class CommandError(ValueError): pass
@dataclass(frozen=True)
class Plan:
    dialect: str
    source: str
    argv: list[list[str]]
    mutating: bool
    description: str
def _prefix(v):
    try: return str(ipaddress.ip_network(v, strict=False))
    except ValueError as e: raise CommandError(f"invalid network prefix: {v}") from e
def _address(v):
    try: return str(ipaddress.ip_address(v))
    except ValueError as e: raise CommandError(f"invalid IP address: {v}") from e
def _mask_prefix(v):
    try: return str(ipaddress.IPv4Network(f"0.0.0.0/{v}").prefixlen)
    except ValueError as e: raise CommandError(f"invalid IPv4 netmask: {v}") from e
def _safe(v):
    if not re.fullmatch(r"[A-Za-z0-9_./:-]{1,64}", v): raise CommandError(f"invalid token: {v}")
    return v
def _route_show(version):
    system=platform.system().lower()
    if system=="linux": return ["ip", "-"+version, "route", "show"]
    if system=="windows": return ["route.exe", "print", "-"+version]
    family="inet6" if version=="6" else "inet"
    return ["netstat", "-rn", "-f", family]
def _interfaces(brief=False):
    system=platform.system().lower()
    if system=="linux": return ["ip", "-brief", "addr"] if brief else ["ip", "-s", "link"]
    if system=="windows": return ["ipconfig.exe", "/all"]
    return ["ifconfig", "-a"]
def _route_change(operation, network, hop=None):
    net=ipaddress.ip_network(network,strict=False)
    system=platform.system().lower()
    if operation=="add" and hop is None: raise CommandError("a next-hop is required to add a route")
    if system=="linux":
        command=["ip","route","replace" if operation=="add" else "del",str(net)]
        if hop is not None: command.extend(["via",hop])
        return command
    if system=="windows":
        if net.version==6:
            return ["route.exe","-6","ADD",str(net),hop] if operation=="add" else ["route.exe","-6","DELETE",str(net)]
        if operation=="add": return ["route.exe","ADD",str(net.network_address),"MASK",str(net.netmask),hop]
        return ["route.exe","DELETE",str(net.network_address)]
    if net.version==6:
        return ["route","-n","-inet6","add",str(net),hop] if operation=="add" else ["route","-n","-inet6","delete",str(net)]
    return ["route","-n","add","-net",str(net),hop] if operation=="add" else ["route","-n","delete","-net",str(net)]
def _frr(*cmds):
    a=["vtysh"]
    for c in cmds: a.extend(["-c",c])
    return a
def _ios(lines):
    argv=[]; cfg=[]; context=None; mut=False; isis_tag=None; isis_net=False
    for raw in lines:
        words=shlex.split(raw)
        if not words: continue
        w=[x.lower() for x in words]
        if w in (["configure","terminal"],["conf","t"]): context="config"; continue
        if w==["end"]: context=None; continue
        if w==["exit"]: context=None; continue
        if w[0]=="show":
            if context: raise CommandError("show cannot be mixed into a configuration block")
            if w[1:]==["ip","route"]: argv.append(_route_show("4"))
            elif w[1:]==["ipv6","route"]: argv.append(_route_show("6"))
            elif w[1:]==["ip","interface","brief"]: argv.append(_interfaces(True))
            elif w[1:]==["ip","protocols"]: argv.append(_frr("show ip protocols"))
            elif w[1:]==["ip","bgp"]: argv.append(_frr("show bgp ipv4 unicast"))
            elif w[1:]==["ip","ospf"]: argv.append(_frr("show ip ospf"))
            elif w[1:]==["standby","brief"]: argv.append(_frr("show vrrp"))
            elif w[1:]==["ip","route","summary"]: argv.append(_route_show("4"))
            elif w[1:] in (["interfaces"],["interface"]): argv.append(_interfaces(False))
            elif w[1:] in (["ip","bgp","summary"],["bgp","summary"]): argv.append(_frr("show bgp ipv4 unicast summary"))
            elif w[1:]==["ipv6","bgp","summary"]: argv.append(_frr("show bgp ipv6 unicast summary"))
            elif w[1:] in (["ip","ospf","neighbor"],["ospf","neighbor"]): argv.append(_frr("show ip ospf neighbor"))
            elif w[1:] in (["isis","neighbors"],["isis","neighbor"]): argv.append(_frr("show isis neighbor"))
            elif w[1:] in (["running-config"],["startup-config"]): argv.append(_frr("show running-config"))
            else: raise CommandError(f"unsupported IOS show command: {raw}")
            continue
        if w[:2]==["ipv6","route"] and len(words)==4:
            net=_prefix(words[2]); hop=_address(words[3])
            if ipaddress.ip_network(net).version!=6 or ipaddress.ip_address(hop).version!=6:
                raise CommandError("ipv6 route requires IPv6 prefix and IPv6 next-hop")
            argv.append(_route_change("add",net,hop)); mut=True; continue
        if w[:3]==["no","ipv6","route"] and len(words)==4:
            net=_prefix(words[3])
            if ipaddress.ip_network(net).version!=6: raise CommandError("no ipv6 route requires an IPv6 prefix")
            argv.append(_route_change("delete",net)); mut=True; continue
        if w[:3]==["no","ip","route"] and len(words)==6:
            net=_prefix(words[3]+"/"+_mask_prefix(words[4])); hop=_address(words[5])
            argv.append(_route_change("delete",net,hop)); mut=True; continue
        if w[:2]==["ip","route"] and len(words)==5:
            net=_prefix(words[2]+"/"+_mask_prefix(words[3])); hop=_address(words[4])
            argv.append(_route_change("add",net,hop)); mut=True; continue
        if w[:2]==["router","bgp"] and len(words)==3:
            asn=int(words[2])
            if not 1<=asn<=4294967295: raise CommandError("BGP ASN out of range")
            cfg.append(f"router bgp {asn}"); context="bgp"; mut=True; continue
        if w[:2]==["router","ospf"] and len(words)==3:
            _safe(words[2]); cfg.append("router ospf"); context="ospf"; mut=True; continue
        if w[:2]==["router","isis"] and len(words) in (2,3):
            isis_tag=_safe(words[2]) if len(words)==3 else "CHIMERA"
            cfg.append(f"router isis {isis_tag}"); context="isis"; mut=True; continue
        if w[0]=="neighbor" and len(words)==4 and w[2]=="remote-as" and context=="bgp":
            asn=int(words[3])
            if not 1<=asn<=4294967295: raise CommandError("peer ASN out of range")
            cfg.append(f"neighbor {_address(words[1])} remote-as {asn}"); mut=True; continue
        if w[0]=="network" and context=="bgp":
            if len(words)==2:
                prefix=_prefix(words[1] if "/" in words[1] else words[1]+"/32")
            elif len(words)==4 and w[2]=="mask":
                prefix=_prefix(words[1]+"/"+_mask_prefix(words[3]))
            else:
                raise CommandError("BGP network syntax: network PREFIX or network ADDRESS mask NETMASK")
            cfg.append(f"network {prefix}"); mut=True; continue
        if w[0]=="network" and context=="ospf" and len(words)==5 and w[3]=="area":
            try:
                ipaddress.IPv4Address(words[1]); ipaddress.IPv4Address(words[2])
            except ValueError as exc:
                raise CommandError("OSPF network and wildcard must be IPv4 addresses") from exc
            cfg.append(f"network {words[1]} {words[2]} area {_safe(words[4])}"); mut=True; continue
        if w[0]=="net" and len(words)==2 and context=="isis":
            if not re.fullmatch(r"(?:[0-9A-Fa-f]{2,4}\.){4,}[0-9A-Fa-f]{2,4}",words[1]):
                raise CommandError("IS-IS NET must be dotted hexadecimal ISO NSAP syntax")
            cfg.append(f"net {words[1]}"); isis_net=True; mut=True; continue
        if w[0]=="passive-interface" and len(words)==2 and context in ("ospf","isis"):
            cfg.append(f"passive-interface {_safe(words[1])}"); mut=True; continue
        if w[0]=="interface" and len(words)==2:
            cfg.append(f"interface {_safe(words[1])}"); context="interface"; mut=True; continue
        if w[:3]==["ip","router","isis"] and len(words)==4 and context=="interface":
            tag=_safe(words[3])
            cfg.append(f"ip router isis {tag}"); mut=True; continue
        if w[:2]==["ip","address"] and context=="interface" and len(words) in (3,4):
            if len(words)==3:
                try: address=str(ipaddress.ip_interface(words[2]))
                except ValueError as e: raise CommandError("interface address must be valid CIDR") from e
            else:
                address=f"{_address(words[2])}/{_mask_prefix(words[3])}"
            cfg.append(f"ip address {address}"); mut=True; continue
        if w[0]=="description" and len(words)>=2 and context:
            desc=" ".join(words[1:])
            if not re.fullmatch(r"[A-Za-z0-9 _.,:/-]{1,80}",desc): raise CommandError("invalid description")
            cfg.append(f"description {desc}"); mut=True; continue
        raise CommandError(f"unsupported or out-of-context IOS command: {raw}")
    if isis_tag and not isis_net: raise CommandError("IS-IS router configuration requires an explicit net <ISO-NET> command")
    if cfg: argv.append(_frr("configure terminal",*cfg,"end"))
    if not argv: raise CommandError("empty command")
    return Plan("ios","\\n".join(lines),argv,mut,"Cisco IOS subset translated to Spotnik/iproute2/FRR")
def _junos(lines):
    argv=[]; cfg=[]; local_as=None; mut=False
    for raw in lines:
        words=shlex.split(raw)
        if not words: continue
        w=[x.lower() for x in words]
        if w[0]=="show":
            if w[1:]==["route"]: argv.append(_route_show("4"))
            elif w[1:]==["route","protocol","bgp"]: argv.append(_frr("show bgp ipv4 unicast"))
            elif w[1:]==["route","protocol","ospf"]: argv.append(_frr("show ip ospf route"))
            elif w[1:]==["route","protocol","isis"]: argv.append(_frr("show isis route"))
            elif w[1:]==["route","summary"]: argv.append(_route_show("4"))
            elif w[1:]==["ospf","neighbor"]: argv.append(_frr("show ip ospf neighbor"))
            elif w[1:]==["isis","adjacency"]: argv.append(_frr("show isis neighbor"))
            elif w[1:]==["bgp","neighbor"]: argv.append(_frr("show bgp ipv4 unicast neighbors"))
            elif w[1:]==["interfaces","terse"]: argv.append(["ip","-brief","addr"])
            elif w[1:]==["bgp","summary"]: argv.append(_frr("show bgp ipv4 unicast summary"))
            elif w[1:]==["configuration"]: argv.append(_frr("show running-config"))
            else: raise CommandError(f"unsupported Junos show command: {raw}")
            continue
        if w[:3]==["set","routing-options","autonomous-system"] and len(words)==4:
            local_as=int(words[3])
            if not 1<=local_as<=4294967295: raise CommandError("local ASN out of range")
            mut=True; continue
        if w[:4]==["set","routing-options","static","route"] and len(words)==7 and w[5]=="next-hop":
            net=_prefix(words[4]); hop=_address(words[6])
            argv.append(_route_change("add",net,hop)); mut=True; continue
        if w[:4]==["delete","routing-options","static","route"] and len(words)==5:
            argv.append(_route_change("delete",_prefix(words[4]))); mut=True; continue
        if w[:4]==["set","protocols","bgp","group"] and len(words)==9 and w[5]=="neighbor" and w[7]=="peer-as":
            if local_as is None: raise CommandError("Junos BGP needs routing-options autonomous-system in this block")
            _safe(words[4]); peer=_address(words[6]); peer_as=int(words[8])
            if not 1<=peer_as<=4294967295: raise CommandError("peer ASN out of range")
            cfg.extend([f"router bgp {local_as}",f"neighbor {peer} remote-as {peer_as}"]); mut=True; continue
        if w[:4]==["set","protocols","ospf","area"] and len(words)==7 and w[5]=="interface":
            area=_safe(words[4]); iface=_safe(words[6])
            cfg.extend(["router ospf",f"interface {iface}",f"ip ospf area {area}"]); mut=True; continue
        if w[:4]==["set","protocols","isis","interface"] and len(words)==5:
            iface=_safe(words[4]); cfg.extend(["router isis CHIMERA",f"interface {iface}"]); mut=True; continue
        raise CommandError(f"unsupported or out-of-context Junos command: {raw}")
    if cfg: argv.append(_frr("configure terminal",*cfg,"end"))
    if not argv: raise CommandError("empty command")
    return Plan("junos","\\n".join(lines),argv,mut,"Junos subset translated to Spotnik/iproute2/FRR")
def translate(dialect,command):
    lines=[x.strip() for x in command.splitlines() if x.strip()]
    if dialect=="ios": return _ios(lines)
    if dialect=="junos": return _junos(lines)
    raise CommandError(f"unknown dialect: {dialect}")
def execute(plan,apply,confirm):
    if plan.mutating and not apply:
        print("REFUSED: mutation is plan-only; pass --apply --confirm "+CONFIRM); return 3
    if plan.mutating and confirm!=CONFIRM:
        print("REFUSED: exact confirmation phrase required: "+CONFIRM); return 3
    if plan.mutating and hasattr(os,"geteuid") and os.geteuid()!=0:
        print("REFUSED: mutations require administrator/root privileges"); return 3
    for argv in plan.argv:
        exe=shutil.which(argv[0])
        if exe is None: print(f"missing backend executable: {argv[0]}",file=sys.stderr); return 127
        result=subprocess.run([exe,*argv[1:]],check=False)
        if result.returncode: return result.returncode
    return 0
def main():
    p=argparse.ArgumentParser(description="Safe Cisco IOS/Junos command compatibility adapter")
    p.add_argument("--dialect",required=True,choices=("ios","junos"))
    p.add_argument("--command",required=True,help="one command or multi-line configuration block")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm")
    a=p.parse_args()
    try: plan=translate(a.dialect,a.command)
    except (CommandError,ValueError) as e: print(f"ERROR: {e}",file=sys.stderr); return 2
    print(json.dumps(asdict(plan),indent=2))
    if a.apply: return execute(plan,True,a.confirm)
    return 3 if plan.mutating else 0
if __name__=="__main__": raise SystemExit(main())
