#include <stdint.h>
#include <chimera/microkernel.h>

namespace {
constexpr uint32_t MAX_CAPS = 128;
constexpr uint32_t MAX_ENDPOINTS = 64;
constexpr uint32_t QUEUE_DEPTH = 16;

enum : uint32_t { CAP_R_SEND = 1u << 0, CAP_R_RECV = 1u << 1, CAP_R_MANAGE = 1u << 2 };

struct Cap { uint32_t owner; uint32_t rights; bool used; };
struct Endpoint {
    chimera_mk_endpoint_handler_t handler;
    chimera_mk_message_t queue[QUEUE_DEPTH];
    uint32_t head;
    uint32_t count;
    chimera_cap_t cap;
    bool used;
};

static Cap caps[MAX_CAPS];
static Endpoint endpoints[MAX_ENDPOINTS];
static bool initialized;

static bool cap_ok(chimera_cap_t c, uint32_t right) {
    if (c == 0 || c > MAX_CAPS) return false;
    const Cap& x = caps[c - 1];
    return x.used && (x.rights & right) != 0;
}
}

extern "C" void chimera_mk_init(void) {
    for (uint32_t i = 0; i < MAX_CAPS; ++i) caps[i] = {0, 0, false};
    for (uint32_t i = 0; i < MAX_ENDPOINTS; ++i) {
        endpoints[i].handler = nullptr;
        endpoints[i].head = endpoints[i].count = 0;
        endpoints[i].cap = 0;
        endpoints[i].used = false;
    }
    initialized = true;
}

extern "C" chimera_cap_t chimera_mk_cap_grant(uint32_t owner, uint32_t rights) {
    if (!initialized) chimera_mk_init();
    for (uint32_t i = 0; i < MAX_CAPS; ++i) {
        if (!caps[i].used) {
            caps[i] = {owner, rights, true};
            return i + 1;
        }
    }
    return 0;
}

extern "C" int chimera_mk_cap_revoke(chimera_cap_t cap) {
    if (cap == 0 || cap > MAX_CAPS || !caps[cap - 1].used) return CHIMERA_MK_INVALID;
    caps[cap - 1] = {0, 0, false};
    return CHIMERA_MK_OK;
}

extern "C" chimera_endpoint_t chimera_mk_endpoint_create(chimera_cap_t cap, chimera_mk_endpoint_handler_t handler) {
    if (!cap_ok(cap, CAP_R_MANAGE)) return 0;
    for (uint32_t i = 0; i < MAX_ENDPOINTS; ++i) {
        if (!endpoints[i].used) {
            endpoints[i].handler = handler;
            endpoints[i].head = endpoints[i].count = 0;
            endpoints[i].cap = cap;
            endpoints[i].used = true;
            return i + 1;
        }
    }
    return 0;
}

extern "C" int chimera_mk_endpoint_send(chimera_endpoint_t endpoint, chimera_cap_t cap, const chimera_mk_message_t* msg) {
    if (!msg || endpoint == 0 || endpoint > MAX_ENDPOINTS || !cap_ok(cap, CAP_R_SEND)) return CHIMERA_MK_INVALID;
    Endpoint& e = endpoints[endpoint - 1];
    if (!e.used || e.count == QUEUE_DEPTH) return CHIMERA_MK_BUSY;
    uint32_t slot = (e.head + e.count) % QUEUE_DEPTH;
    e.queue[slot] = *msg;
    ++e.count;
    /* Endpoint send only enqueues. Service code must execute in its own
       schedulable context; invoking a handler here would run service logic
       inside the sender's kernel call path and defeats isolation. */
    return CHIMERA_MK_OK;
}

extern "C" int chimera_mk_endpoint_receive(chimera_endpoint_t endpoint, chimera_cap_t cap, chimera_mk_message_t* msg) {
    if (!msg || endpoint == 0 || endpoint > MAX_ENDPOINTS || !cap_ok(cap, CAP_R_RECV)) return CHIMERA_MK_INVALID;
    Endpoint& e = endpoints[endpoint - 1];
    if (!e.used || e.count == 0) return CHIMERA_MK_EMPTY;
    *msg = e.queue[e.head];
    e.head = (e.head + 1) % QUEUE_DEPTH;
    --e.count;
    return CHIMERA_MK_OK;
}

extern "C" int64_t chimera_mk_syscall(uint64_t number, uint64_t arg0, uint64_t arg1, uint64_t arg2, uint64_t arg3) {
    switch (number) {
        case 0: chimera_mk_init(); return CHIMERA_MK_OK;
        case 1: return (int64_t)chimera_mk_cap_grant((uint32_t)arg0, (uint32_t)arg1);
        case 2: return chimera_mk_cap_revoke((chimera_cap_t)arg0);
        case 3: return (int64_t)chimera_mk_endpoint_send((chimera_endpoint_t)arg0, (chimera_cap_t)arg1, (const chimera_mk_message_t*)arg2);
        case 4: return chimera_mk_endpoint_receive((chimera_endpoint_t)arg0, (chimera_cap_t)arg1, (chimera_mk_message_t*)arg2);
        case 5: return (int64_t)chimera_mk_endpoint_create((chimera_cap_t)arg0, (chimera_mk_endpoint_handler_t)arg1);
        default: (void)arg3; return CHIMERA_MK_INVALID;
    }
}
