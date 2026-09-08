#pragma once
#ifndef CHIMERA_NETINET_IP_H
#define CHIMERA_NETINET_IP_H
#include <stdint.h>
#include <netinet/in.h>

struct iphdr {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    uint8_t ihl:4; uint8_t version:4;
#else
    uint8_t version:4; uint8_t ihl:4;
#endif
    uint8_t tos;
    uint16_t tot_len;
    uint16_t id;
    uint16_t frag_off;
    uint8_t ttl;
    uint8_t protocol;
    uint16_t check;
    uint32_t saddr;
    uint32_t daddr;
};
#define IPVERSION 4
#define IP_MAXPACKET 65535
#define IP_DF 0x4000
#define IP_MF 0x2000
#define IP_OFFMASK 0x1FFF
#endif
