# Koronos / Spotnik routing and SDN

Chimera II OS now defines routing as an OS capability rather than an application concern.

## Stack

`Application → session/RPC → Spotnik socket API → TCP/UDP → IPv4/IPv6 → route table → interface/driver`

Dynamic control plane:

`RIP/RIPng | OSPFv2/v3 | IS-IS | BGP4 | EIGRP adapter | Babel | BFD | VRRP | PIM | OpenFabric | BGP-LS`

SDN/control:

`OpenFlow | P4Runtime | NETCONF | RESTCONF | gNMI | Envoy xDS`

The design follows the capability boundary used by FRRouting rather than embedding its daemon implementation. FRR currently documents BGP, RIP, OSPF, IS-IS, BFD, Babel, PIM, OpenFabric, VRRP and alpha EIGRP support; BGP-LS is documented as a topology distribution mechanism useful to SDN controllers and traffic engineering. citeturn0search6turn0search1

## IPv4/IPv6

- Dual-stack route tables.
- ARP for IPv4 and Neighbor Discovery for IPv6.
- ICMP/ICMPv6 control messages.
- TCP/UDP sockets above IP.
- MTU/path-MTU awareness.
- Route expiry and administrative distance.
- Static routes are safe-by-default; dynamic routing requires explicit policy.

## Local routing

Every application can request a local route lookup through Spotnik without starting a routing daemon. The route manager supports static, connected and policy-selected routes.

## Dynamic routing

Dynamic protocol engines are OS services. They advertise/withdraw routes through a single RIB/FIB API. Protocol-specific wire parsing, timers, authentication and neighbor state remain isolated in their adapters.

## SDN

An optional controller can push versioned policy to the OS. Envoy xDS is reserved for application/service traffic rather than kernel routing; its dynamic resource model supports listeners, routes, clusters and endpoints through gRPC or REST. citeturn1search3turn1search9

## Failure handling

- BFD may provide fast liveness detection.
- Route changes are atomic at the RIB/FIB boundary.
- Failed control-plane updates are rejected without replacing the last known-good table.
- Configuration changes are versioned and auditable.
- No application is allowed to modify host routing tables directly unless explicitly granted a capability.
