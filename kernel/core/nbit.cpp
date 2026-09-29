#include "chimera/nbit.h"
#include "chimera/hardware.h"
#include <stddef.h>

static chimera_hardware_profile g_profile;
static uint32_t g_default_mode = CHIMERA_NBIT_64;

static int valid_mode(uint32_t bits) {
    switch (bits) {
        case 8: case 16: case 32: case 64: case 128: case 256:
        case 512: case 1024: case 2048: case 4096: case 8192: return 1;
        default: return 0;
    }
}

extern "C" int chimera_nbit_init(void) {
    if (chimera_hardware_probe(&g_profile) != 0) return -1;
    g_default_mode = (uint32_t)chimera_hardware_best_mode(&g_profile);
    return 0;
}

extern "C" int chimera_nbit_get_default(uint32_t *bits) {
    if (!bits) return -1;
    *bits = g_default_mode;
    return 0;
}

extern "C" int chimera_nbit_set_default(uint32_t bits) {
    if (!valid_mode(bits)) return -1;
    if (!chimera_hardware_supports_mode(&g_profile, bits)) return -2;
    g_default_mode = bits;
    return 0;
}

extern "C" int chimera_nbit_validate(uint32_t bits) {
    return valid_mode(bits) ? 0 : -1;
}

extern "C" int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits, uint32_t compatibility_target) {
    if (!ctx) return -1;
    uint32_t mode = requested_bits ? requested_bits : g_default_mode;
    if (!valid_mode(mode)) return -2;
    if (!chimera_hardware_supports_mode(&g_profile, mode)) return -3;
    ctx->process_id = process_id;
    ctx->mode_bits = mode;
    ctx->execution_class = (mode == g_profile.native_nbit_mode) ? CHIMERA_EXEC_NATIVE : CHIMERA_EXEC_EMULATED;
    ctx->compatibility_target = compatibility_target;
    ctx->abi_version = CHIMERA_NBIT_CONTEXT_VERSION;
    ctx->flags = 0;
    return 0;
}

extern "C" int chimera_nbit_process_set_mode(chimera_nbit_process_context *ctx, uint32_t bits) {
    if (!ctx || !valid_mode(bits)) return -1;
    if (!chimera_hardware_supports_mode(&g_profile, bits)) return -2;
    ctx->mode_bits = bits;
    ctx->execution_class = (bits == g_profile.native_nbit_mode) ? CHIMERA_EXEC_NATIVE : CHIMERA_EXEC_EMULATED;
    return 0;
}

extern "C" int chimera_nbit_process_set_compatibility(chimera_nbit_process_context *ctx, uint32_t target) {
    if (!ctx || !(target & g_profile.compatibility_mask)) return -1;
    ctx->compatibility_target = target;
    ctx->execution_class = CHIMERA_EXEC_COMPATIBILITY;
    return 0;
}

extern "C" int chimera_nbit_ipc_validate(const chimera_ipc_wire *wire) {
    if (!wire || wire->version != CHIMERA_NBIT_CONTEXT_VERSION || !wire->payload) return -1;
    if (!valid_mode(wire->sender_mode_bits) || !valid_mode(wire->receiver_mode_bits)) return -2;
    if (wire->payload_bytes > (wire->payload_bits + 7u) / 8u) return -3;
    if (wire->payload_bytes > (16u * 1024u * 1024u)) return -4;
    return 0;
}
