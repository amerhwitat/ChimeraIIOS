#include "chimera/nbit.h"
#include "chimera/hardware.h"
#include <stddef.h>

static chimera_hardware_profile g_profile;
static uint32_t g_default_mode = CHIMERA_NBIT_64;
static chimera_nbit_process_context g_processes[CHIMERA_NBIT_MAX_PROCESS_MODES];
static uint32_t g_process_count = 0;
static uint32_t g_registry_lock = 0;\nstatic uint32_t g_init_lock = 0;\nstatic uint32_t g_init_state = 0;

static void registry_lock(void) {
    while (__sync_lock_test_and_set(&g_registry_lock, 1u)) { }
}
static void registry_unlock(void) { __sync_lock_release(&g_registry_lock); }

static int valid_mode(uint32_t bits) {
    /* The virtual ABI accepts arbitrary positive widths, not only powers of two.
       Runtime memory and scheduler policy impose practical per-process limits. */
    return bits >= CHIMERA_NBIT_MODE_MIN_BITS && bits <= CHIMERA_NBIT_MODE_MAX_BITS;
}
static int find_process_locked(uint32_t process_id) {
    if (!process_id) return -1;
    for (uint32_t i = 0; i < g_process_count; ++i)
        if (g_processes[i].process_id == process_id) return (int)i;
    return -1;
}
static int store_process(const chimera_nbit_process_context *ctx) {
    if (!ctx || !ctx->process_id || ctx->abi_version != CHIMERA_NBIT_CONTEXT_VERSION ||
        !valid_mode(ctx->mode_bits)) return -1;
    registry_lock();
    int i = find_process_locked(ctx->process_id);
    if (i >= 0) {
        g_processes[(uint32_t)i] = *ctx;
        registry_unlock();
        return 0;
    }
    if (g_process_count >= CHIMERA_NBIT_MAX_PROCESS_MODES) {
        registry_unlock();
        return -2;
    }
    g_processes[g_process_count++] = *ctx;
    registry_unlock();
    return 0;
}

extern "C" int chimera_nbit_init(void) {
    while (__sync_lock_test_and_set(&g_init_lock, 1u)) { }
    if (g_init_state == 1u) { __sync_lock_release(&g_init_lock); return 0; }
    if (chimera_hardware_probe(&g_profile) != 0) {
        __sync_lock_release(&g_init_lock);
        return -1;
    }
    uint32_t best = (uint32_t)chimera_hardware_best_mode(&g_profile);
    if (!valid_mode(best)) best = CHIMERA_NBIT_64;
    registry_lock();
    g_default_mode = best;
    registry_unlock();
    g_init_state = 1u;
    __sync_lock_release(&g_init_lock);
    return 0;
}
extern "C" int chimera_nbit_get_default(uint32_t *bits) {
    if (!bits) return -1;
    registry_lock();
    *bits = g_default_mode;
    registry_unlock();
    return 0;
}
extern "C" int chimera_nbit_set_default(uint32_t bits) {
    if (!valid_mode(bits)) return -1;
    if (chimera_nbit_init() != 0) return -3;
    if (!chimera_hardware_supports_mode(&g_profile, bits)) return -2;
    registry_lock();
    g_default_mode = bits;
    registry_unlock();
    return 0;
}
extern "C" int chimera_nbit_validate(uint32_t bits) { return valid_mode(bits) ? 0 : -1; }

extern "C" int chimera_nbit_get_capabilities(chimera_nbit_capabilities *out) {
    if (!out) return -1;
    if (chimera_nbit_init() != 0) return -2;
    out->native_hardware_bits = g_profile.native_nbit_mode;
    out->default_mode_bits = g_default_mode;
    out->minimum_virtual_bits = CHIMERA_NBIT_MODE_MIN_BITS;
    out->maximum_virtual_bits = CHIMERA_NBIT_MODE_MAX_BITS;
    out->registered_process_capacity = CHIMERA_NBIT_MAX_PROCESS_MODES;
    out->flags = CHIMERA_NBIT_CAP_ARBITRARY_WIDTH |
                 CHIMERA_NBIT_CAP_CHIMERA_VIRTUAL_ABI |
                 CHIMERA_NBIT_CAP_PHYSICAL_NATIVE_IS_HARDWARE_ONLY;
    return 0;
}

extern "C" int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id,
                                           uint32_t requested_bits, uint32_t compatibility_target) {
    if (!ctx || !process_id) return -1;
    if (chimera_nbit_init() != 0) return -4;
    uint32_t mode = requested_bits ? requested_bits : g_default_mode;
    if (!valid_mode(mode)) return -2;
    if (compatibility_target & ~g_profile.compatibility_mask) return -5;
    if (!chimera_hardware_supports_mode(&g_profile, mode)) return -3;
    ctx->process_id = process_id;
    ctx->mode_bits = mode;
    ctx->execution_class = (mode == g_profile.native_nbit_mode && compatibility_target == 0)
        ? CHIMERA_EXEC_NATIVE
        : (compatibility_target ? CHIMERA_EXEC_COMPATIBILITY : CHIMERA_EXEC_EMULATED);
    ctx->compatibility_target = compatibility_target;
    ctx->abi_version = CHIMERA_NBIT_CONTEXT_VERSION;
    ctx->flags = 0;
    return store_process(ctx);
}

extern "C" int chimera_nbit_process_init_chimera(chimera_nbit_process_context *ctx,
                                                    uint32_t process_id,
                                                    uint32_t requested_bits) {
    if (!ctx || !process_id) return -1;
    if (chimera_nbit_init() != 0) return -4;
    const uint32_t mode = requested_bits ? requested_bits : g_default_mode;
    if (!valid_mode(mode)) return -2;
    if (!chimera_hardware_supports_mode(&g_profile, mode)) return -3;
    ctx->process_id = process_id;
    ctx->mode_bits = mode;
    ctx->execution_class = CHIMERA_EXEC_CHIMERA_VIRTUAL;
    ctx->compatibility_target = 0;
    ctx->abi_version = CHIMERA_NBIT_CONTEXT_VERSION;
    ctx->flags = 1u; /* Native to the Chimera virtual ABI, not physical CPU hardware. */
    return store_process(ctx);
}
extern "C" int chimera_nbit_process_set_mode(chimera_nbit_process_context *ctx, uint32_t bits) {
    if (!ctx || !valid_mode(bits)) return -1;
    if (!chimera_hardware_supports_mode(&g_profile, bits)) return -2;
    ctx->mode_bits = bits;
    ctx->execution_class = ctx->compatibility_target
        ? CHIMERA_EXEC_COMPATIBILITY
        : ((ctx->flags & 1u) ? CHIMERA_EXEC_CHIMERA_VIRTUAL
           : ((bits == g_profile.native_nbit_mode) ? CHIMERA_EXEC_NATIVE : CHIMERA_EXEC_EMULATED));
    return store_process(ctx);
}
extern "C" int chimera_nbit_process_set_compatibility(chimera_nbit_process_context *ctx, uint32_t target) {
    if (!ctx || !(target & g_profile.compatibility_mask) ||
        (target & ~g_profile.compatibility_mask)) return -1;
    ctx->compatibility_target = target;
    ctx->flags &= ~1u;
    ctx->execution_class = CHIMERA_EXEC_COMPATIBILITY;
    return store_process(ctx);
}
extern "C" int chimera_nbit_process_unregister(uint32_t process_id) {
    registry_lock();
    int found = find_process_locked(process_id);
    if (found < 0) { registry_unlock(); return -1; }
    uint32_t i = (uint32_t)found;
    g_processes[i] = g_processes[g_process_count - 1u];
    g_processes[g_process_count - 1u] = {};
    --g_process_count;
    registry_unlock();
    return 0;
}
extern "C" int chimera_nbit_process_get(uint32_t process_id, chimera_nbit_process_context *out) {
    if (!out) return -1;
    registry_lock();
    int found = find_process_locked(process_id);
    if (found >= 0) *out = g_processes[(uint32_t)found];
    registry_unlock();
    return found >= 0 ? 0 : -2;
}
extern "C" uint32_t chimera_nbit_process_snapshot(chimera_nbit_process_context *out, uint32_t capacity) {
    if (!out || !capacity) return 0;
    registry_lock();
    uint32_t n = g_process_count < capacity ? g_process_count : capacity;
    for (uint32_t i = 0; i < n; ++i) out[i] = g_processes[i];
    registry_unlock();
    return n;
}
extern "C" int chimera_nbit_registry_get_snapshot(chimera_nbit_registry_snapshot *out) {
    if (!out) return -1;
    registry_lock();
    out->abi_version = CHIMERA_NBIT_CONTEXT_VERSION;
    out->registered_processes = g_process_count;
    out->capacity = CHIMERA_NBIT_MAX_PROCESS_MODES;
    out->default_mode_bits = g_default_mode;
    registry_unlock();
    return 0;
}
extern "C" int chimera_nbit_ipc_prepare(uint32_t sender_id, uint32_t receiver_id,
                                          const void *payload, uint32_t payload_bits,
                                          uint64_t sequence, chimera_ipc_wire *out) {
    if (!out || !payload || !payload_bits) return -1;
    chimera_nbit_process_context sender{}, receiver{};
    if (chimera_nbit_process_get(sender_id, &sender) != 0 ||
        chimera_nbit_process_get(receiver_id, &receiver) != 0) return -2;
    uint64_t bytes64 = ((uint64_t)payload_bits + 7u) / 8u;
    if (bytes64 > 16u * 1024u * 1024u) return -3;
    out->version = CHIMERA_NBIT_CONTEXT_VERSION;
    out->sender_mode_bits = sender.mode_bits;
    out->receiver_mode_bits = receiver.mode_bits;
    out->payload_bits = payload_bits;
    out->payload_bytes = (uint32_t)bytes64;
    out->sequence = sequence;
    out->payload = payload;
    return chimera_nbit_ipc_validate(out);
}
extern "C" int chimera_nbit_ipc_validate(const chimera_ipc_wire *wire) {
    if (!wire || wire->version != CHIMERA_NBIT_CONTEXT_VERSION) return -1;
    if (!valid_mode(wire->sender_mode_bits) || !valid_mode(wire->receiver_mode_bits)) return -2;
    if (!wire->payload_bits || !wire->payload || !wire->payload_bytes) return -3;
    uint64_t expected = ((uint64_t)wire->payload_bits + 7u) / 8u;
    if (expected > 16u * 1024u * 1024u || wire->payload_bytes != expected) return -4;
    return 0;
}

extern "C" int chimera_nbit_ipc_copy_payload(const chimera_ipc_wire *wire,
                                               void *receiver_buffer,
                                               uint32_t receiver_capacity) {
    if (chimera_nbit_ipc_validate(wire) != 0) return -1;
    if (!receiver_buffer || receiver_capacity < wire->payload_bytes) return -2;
    const uint8_t *src = static_cast<const uint8_t *>(wire->payload);
    uint8_t *dst = static_cast<uint8_t *>(receiver_buffer);
    for (uint32_t i = 0; i < wire->payload_bytes; ++i) dst[i] = src[i];
    return (int)wire->payload_bytes;
}
