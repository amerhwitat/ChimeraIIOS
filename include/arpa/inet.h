#pragma once
#ifndef CHIMERA_POSIX_ARPA_INET_H
#define CHIMERA_POSIX_ARPA_INET_H

#include <stddef.h>
#include <stdint.h>
#include <netinet/in.h>

#ifdef __cplusplus
extern "C" {
#endif

uint32_t chimera_htonl(uint32_t hostlong);
uint16_t chimera_htons(uint16_t hostshort);
uint32_t chimera_ntohl(uint32_t netlong);
uint16_t chimera_ntohs(uint16_t netshort);
int chimera_inet_pton(int af, const char *src, void *dst);
const char *chimera_inet_ntop(int af, const void *src, char *dst, size_t size);
int chimera_inet_aton(const char *cp, struct in_addr *inp);
uint32_t chimera_inet_addr(const char *cp);

#ifndef CHIMERA_USE_SYSTEM_INET
#define htonl chimera_htonl
#define htons chimera_htons
#define ntohl chimera_ntohl
#define ntohs chimera_ntohs
#define inet_pton chimera_inet_pton
#define inet_ntop chimera_inet_ntop
#define inet_aton chimera_inet_aton
#define inet_addr chimera_inet_addr
#endif

#ifdef __cplusplus
}
#endif

#endif
