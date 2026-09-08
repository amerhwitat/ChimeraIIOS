#pragma once
#ifndef CHIMERA_NETINET_IN_H
#define CHIMERA_NETINET_IN_H

#include <stdint.h>
#include <sys/socket.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint16_t in_port_t;
typedef uint32_t in_addr_t;

struct in_addr { in_addr_t s_addr; };
struct in6_addr { uint8_t s6_addr[16]; };
struct sockaddr_in {
    sa_family_t sin_family;
    in_port_t sin_port;
    struct in_addr sin_addr;
    unsigned char sin_zero[8];
};
struct sockaddr_in6 {
    sa_family_t sin6_family;
    in_port_t sin6_port;
    uint32_t sin6_flowinfo;
    struct in6_addr sin6_addr;
    uint32_t sin6_scope_id;
};
struct ipv6_mreq {
    struct in6_addr ipv6mr_multiaddr;
    unsigned int ipv6mr_interface;
};

#ifndef AF_INET
#define AF_INET 2
#endif
#ifndef AF_INET6
#define AF_INET6 10
#endif
#ifndef IPPROTO_IP
#define IPPROTO_IP 0
#endif
#ifndef IPPROTO_ICMP
#define IPPROTO_ICMP 1
#endif
#ifndef IPPROTO_TCP
#define IPPROTO_TCP 6
#endif
#ifndef IPPROTO_UDP
#define IPPROTO_UDP 17
#endif
#ifndef IPPROTO_IPV6
#define IPPROTO_IPV6 41
#endif
#ifndef IPPROTO_RAW
#define IPPROTO_RAW 255
#endif

#define INADDR_ANY       ((in_addr_t)0x00000000U)
#define INADDR_BROADCAST ((in_addr_t)0xFFFFFFFFU)
#define INADDR_LOOPBACK  ((in_addr_t)0x7F000001U)
#define INADDR_NONE      ((in_addr_t)0xFFFFFFFFU)
#define INET_ADDRSTRLEN  16
#define INET6_ADDRSTRLEN 46

#define IN6ADDR_ANY_INIT      { { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 } }
#define IN6ADDR_LOOPBACK_INIT { { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 } }

#ifdef __cplusplus
}
#endif

#endif
