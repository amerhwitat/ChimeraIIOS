# Chimera II POSIX Internet-header compatibility

Chimera II now provides a project-owned Internet address compatibility layer under the standard include paths:

- `include/arpa/inet.h`
- `include/netinet/in.h`
- `include/netinet/ip.h`
- `include/netinet/ip6.h`
- `include/netinet/tcp.h`
- `include/netinet/udp.h`
- `src/net/inet.cpp`

The interfaces cover the core byte-order and address-conversion surface needed by the network stack and userspace ports: `htonl`, `htons`, `ntohl`, `ntohs`, `inet_pton`, `inet_ntop`, `inet_aton`, and `inet_addr`, with IPv4 and IPv6 address structures and protocol constants.

## ABI policy

This addition is additive. Existing Chimera II ABI entry points are unchanged. The new functions use `chimera_*` symbols and the public `arpa/inet.h` compatibility header maps the standard names to those symbols unless `CHIMERA_USE_SYSTEM_INET` is defined.

## Standards alignment

The header layout and core types follow the POSIX `netinet/in.h` model. POSIX specifies `in_port_t`, `in_addr_t`, `in_addr`, `sockaddr_in`, `in6_addr`, and `sockaddr_in6`, while Linux documents `inet_pton`/`inet_ntop` as the IPv4/IPv6 text-to-binary and binary-to-text conversion interfaces. See the POSIX and Linux references below.

- POSIX Programmer's Manual: `netinet/in.h`
- Linux man-pages: `inet(3)`
- Linux man-pages: `inet_pton(3)`
- Linux `ip(7)`

## Build integration

`src/net/inet.cpp` is part of `chimera_machine`, and `tests/unit/test_inet.cpp` is registered as the `chimera_inet` CTest. The test covers byte-order conversion, IPv4 round-trip, IPv6 compressed-address round-trip, invalid-address rejection, and unsupported address-family handling.

## Scope note

This layer intentionally implements the portable address-conversion subset first. Legacy classful helpers and resolver/database APIs such as `getaddrinfo`, `gethostbyname`, and `getnameinfo` belong in the resolver module rather than the low-level Internet-address header layer.
