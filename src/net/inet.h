#pragma once

#include <arpa/inet.h>
#include <cstddef>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

uint16_t chimera_htons(uint16_t v);
uint16_t chimera_ntohs(uint16_t v);
uint32_t chimera_htonl(uint32_t v);
uint32_t chimera_ntohl(uint32_t v);

int chimera_inet_pton(int af, const char* src, void* dst);
const char* chimera_inet_ntop(int af, const void* src, char* dst, std::size_t size);
int chimera_inet_aton(const char* cp, struct in_addr* inp);
uint32_t chimera_inet_addr(const char* cp);

#ifdef __cplusplus
}
#endif
