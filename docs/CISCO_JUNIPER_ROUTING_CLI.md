# Cisco IOS and Juniper Junos command compatibility

Chimera exposes a bounded vendor-dialect adapter for network engineers. It translates selected Cisco IOS and Juniper Junos commands into Spotnik route operations, Linux iproute2 or FRRouting (FRR) commands.

## Usage

    chimera-router-cli --dialect ios --command "show ip route"
    chimera-router-cli --dialect junos --command "show route protocol bgp"

    # Plan a static route; this does not change the host
    chimera-router-cli --dialect ios --command "ip route 10.10.0.0 255.255.0.0 192.0.2.1"

    # Mutations require root plus explicit confirmation
    sudo chimera-router-cli --dialect ios --command "ip route 10.10.0.0 255.255.0.0 192.0.2.1" --apply --confirm APPLY-ROUTING-CHANGES

## Supported command families

| Vendor dialect | Supported subset |
|---|---|
| Cisco IOS | show routes/interfaces, BGP summary, OSPF neighbors, IS-IS neighbors, running config, static routes, basic BGP/OSPF configuration; IS-IS only with an explicit NET and interface mapping, interface descriptions and IP addresses |
| Juniper Junos | show route, BGP/OSPF route views, show interfaces terse, BGP summary, configuration view, static routes, BGP neighbor and basic OSPF interface configuration; IS-IS is show-only until NET/interface mapping is available |

This is a compatibility subset, not a complete Cisco IOS-XE/NX-OS or Junos CLI implementation. Junos candidate configuration, confirmed commit, rollback, routing policy language, firewall filters, MPLS traffic-engineering policy and vendor-specific hardware commands are not translated.

## Protocol and backend coverage

- Static IPv4/IPv6 routes use native host route commands: iproute2 on Linux, route/netstat on FreeBSD and macOS, and route.exe on Windows. The Spotnik RIB/FIB interface is the BareMetal target contract.
- Dynamic routing uses FRR daemons through vtysh when installed and enabled: BGP, OSPF, IS-IS, RIP/RIPng, Babel, BFD, PIM, VRRP and OpenFabric according to the selected FRR build.
- EVPN/VXLAN, BGP-LS, segment routing and SDN controller interfaces require their own backend and conformance tests; a protocol catalog entry alone is not proof of implementation.
- EIGRP remains experimental and is not enabled by default.
- Dynamic neighbors and route advertisements remain disabled until an administrator explicitly configures the protocol and its security policy.

## Security boundary

The adapter selects native route/interface commands on Linux, FreeBSD, macOS and Windows. It rejects unrecognized syntax, avoids shell interpolation, validates IP addresses/prefixes, and requires explicit apply, the exact confirmation phrase APPLY-ROUTING-CHANGES, and administrator privileges for mutations. Review generated plans before applying them on production routers or hosts.
