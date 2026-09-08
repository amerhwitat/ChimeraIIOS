#pragma once
#ifndef CHIMERA_NETINET_IP6_H
#define CHIMERA_NETINET_IP6_H
#include <stdint.h>
#include <netinet/in.h>

struct ip6_hdr {
    union { uint8_t u6_vfc; uint32_t u6_flow; } ip6_ctlun;
    uint16_t ip6_plen;
    uint8_t ip6_nxt;
    uint8_t ip6_hlim;
    struct in6_addr ip6_src;
    struct in6_addr ip6_dst;
};
#define ip6_vfc   ip6_ctlun.u6_vfc
#define ip6_flow   ip6_ctlun.u6_flow
#define IP6VERSION 6
#define IPV6_MINHOPCOUNT 1
#endif
