#pragma once
/*
 * Canonical serialized microkernel message ABI.
 * Wire order is little-endian on every host/guest architecture.
 * This is deliberately separate from the native in-memory struct layout.
 */
#include <stdint.h>
#include "microkernel.h"
#include "endianness.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_MK_MESSAGE_WIRE_SIZE 40u

static inline int chimera_mk_message_encode_le(
    uint8_t *dst, uint32_t dst_size, const chimera_mk_message_t *msg) {
    if (!dst || !msg || dst_size < CHIMERA_MK_MESSAGE_WIRE_SIZE) return -1;
    chimera_store_le32(dst + 0, msg->opcode);
    chimera_store_le32(dst + 4, msg->flags);
    chimera_store_le64(dst + 8, msg->arg0);
    chimera_store_le64(dst + 16, msg->arg1);
    chimera_store_le64(dst + 24, msg->arg2);
    chimera_store_le64(dst + 32, msg->arg3);
    return (int)CHIMERA_MK_MESSAGE_WIRE_SIZE;
}

static inline int chimera_mk_message_decode_le(
    const uint8_t *src, uint32_t src_size, chimera_mk_message_t *msg) {
    if (!src || !msg || src_size < CHIMERA_MK_MESSAGE_WIRE_SIZE) return -1;
    msg->opcode = chimera_load_le32(src + 0);
    msg->flags = chimera_load_le32(src + 4);
    msg->arg0 = chimera_load_le64(src + 8);
    msg->arg1 = chimera_load_le64(src + 16);
    msg->arg2 = chimera_load_le64(src + 24);
    msg->arg3 = chimera_load_le64(src + 32);
    return (int)CHIMERA_MK_MESSAGE_WIRE_SIZE;
}

#ifdef __cplusplus
}
#endif
