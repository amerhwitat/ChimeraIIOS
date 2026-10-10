#pragma once
/*
 * Chimera endian-safe wire helpers.
 * CPU-native memory order is not the same as the canonical IPC/boot wire order.
 * These helpers are freestanding and do not rely on host byte order.
 */
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum chimera_endian {
    CHIMERA_ENDIAN_UNKNOWN = 0,
    CHIMERA_ENDIAN_LITTLE = 1,
    CHIMERA_ENDIAN_BIG = 2
} chimera_endian_t;

static inline uint16_t chimera_bswap16(uint16_t x) {
    return (uint16_t)((x << 8) | (x >> 8));
}
static inline uint32_t chimera_bswap32(uint32_t x) {
    return ((x & UINT32_C(0x000000FF)) << 24) |
           ((x & UINT32_C(0x0000FF00)) << 8)  |
           ((x & UINT32_C(0x00FF0000)) >> 8)  |
           ((x & UINT32_C(0xFF000000)) >> 24);
}
static inline uint64_t chimera_bswap64(uint64_t x) {
    return ((uint64_t)chimera_bswap32((uint32_t)x) << 32) |
           chimera_bswap32((uint32_t)(x >> 32));
}

static inline uint16_t chimera_load_le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static inline uint32_t chimera_load_le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static inline uint64_t chimera_load_le64(const uint8_t *p) {
    return (uint64_t)chimera_load_le32(p) |
           ((uint64_t)chimera_load_le32(p + 4) << 32);
}
static inline void chimera_store_le16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8);
}
static inline void chimera_store_le32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}
static inline void chimera_store_le64(uint8_t *p, uint64_t v) {
    chimera_store_le32(p, (uint32_t)v);
    chimera_store_le32(p + 4, (uint32_t)(v >> 32));
}
static inline uint16_t chimera_load_be16(const uint8_t *p) {
    return (uint16_t)(((uint16_t)p[0] << 8) | p[1]);
}
static inline uint32_t chimera_load_be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}
static inline uint64_t chimera_load_be64(const uint8_t *p) {
    return ((uint64_t)chimera_load_be32(p) << 32) |
           chimera_load_be32(p + 4);
}
static inline void chimera_store_be16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v;
}
static inline void chimera_store_be32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v;
}
static inline void chimera_store_be64(uint8_t *p, uint64_t v) {
    chimera_store_be32(p, (uint32_t)(v >> 32));
    chimera_store_be32(p + 4, (uint32_t)v);
}

/* Safe runtime probe for the byte order of the currently executing CPU mode. */
static inline chimera_endian_t chimera_native_endian(void) {
    const uint16_t one = 1;
    const uint8_t *p = (const uint8_t *)&one;
    if (p[0] == 1) return CHIMERA_ENDIAN_LITTLE;
    if (p[0] == 0 && p[1] == 1) return CHIMERA_ENDIAN_BIG;
    return CHIMERA_ENDIAN_UNKNOWN;
}

#ifdef __cplusplus
}
#endif
