#include "../include/chimera/service.h"

namespace {
struct service_state { const char* id; uint32_t state; };
static service_state g_states[CHIMERA_SERVICE_MAX];
static uint32_t g_state_count = 0;

static bool same(const char* a, const char* b) {
    if (!a || !b) return false;
    while (*a && *b && *a == *b) { ++a; ++b; }
    return *a == 0 && *b == 0;
}
static int find(const chimera_service_manifest* services, uint32_t count, const char* id) {
    if (!services || !id) return -1;
    for (uint32_t i = 0; i < count; ++i)
        if (same(services[i].id, id)) return static_cast<int>(i);
    return -1;
}
static bool dependencies_running(const chimera_service_manifest* services, uint32_t index) {
    for (uint32_t d = 0; d < services[index].dependency_count; ++d)
        if (chimera_service_get_state(services[index].dependencies[d]) != CHM_SVC_RUNNING)
            return false;
    return true;
}
static int run_one(const char* id, const chimera_service_ops* ops) {
    if (ops->start(id, ops->context) != 0) {
        if (ops->stop) (void)ops->stop(id, ops->context);
        return -1;
    }
    if (ops->health(id, ops->context) != 0) {
        if (ops->stop) (void)ops->stop(id, ops->context);
        return -2;
    }
    return 0;
}
}

extern "C" int chimera_service_validate(const chimera_service_manifest* services, uint32_t count) {
    if (!services || !count || count > CHIMERA_SERVICE_MAX) return -1;
    for (uint32_t i = 0; i < count; ++i) {
        if (services[i].abi_version != CHIMERA_SERVICE_ABI || !services[i].id ||
            services[i].restart > CHM_RESTART_FAILURE ||
            (services[i].dependency_count && !services[i].dependencies) ||
            services[i].dependency_count > count) return -2;
        for (uint32_t j = i + 1; j < count; ++j)
            if (same(services[i].id, services[j].id)) return -3;
        for (uint32_t d = 0; d < services[i].dependency_count; ++d)
            if (!services[i].dependencies[d] ||
                find(services, count, services[i].dependencies[d]) < 0) return -4;
    }
    return 0;
}

extern "C" int chimera_service_resolve(const chimera_service_manifest* services, uint32_t count,
                                        chimera_service_plan* plan) {
    if (!plan || !plan->ordered_ids || count > CHIMERA_SERVICE_MAX || plan->capacity < count)
        return -1;
    const int valid = chimera_service_validate(services, count);
    if (valid < 0) return valid;
    uint8_t done[CHIMERA_SERVICE_MAX] = {};
    plan->count = 0;
    while (plan->count < count) {
        bool progressed = false;
        for (uint32_t i = 0; i < count; ++i) {
            if (done[i]) continue;
            bool ready = true;
            for (uint32_t d = 0; d < services[i].dependency_count; ++d) {
                const int dependency = find(services, count, services[i].dependencies[d]);
                if (dependency < 0 || !done[static_cast<uint32_t>(dependency)]) {
                    ready = false;
                    break;
                }
            }
            if (ready) {
                done[i] = 1;
                plan->ordered_ids[plan->count++] = services[i].id;
                progressed = true;
            }
        }
        if (!progressed) return -6; /* missing progress means a dependency cycle */
    }
    return 0;
}

extern "C" int chimera_service_set_state(const char* id, uint32_t state) {
    if (!id || state > CHM_SVC_RECOVERING) return -1;
    for (uint32_t i = 0; i < g_state_count; ++i) {
        if (same(g_states[i].id, id)) {
            g_states[i].state = state;
            return 0;
        }
    }
    if (g_state_count >= CHIMERA_SERVICE_MAX) return -2;
    g_states[g_state_count++] = {id, state};
    return 0;
}

extern "C" uint32_t chimera_service_get_state(const char* id) {
    for (uint32_t i = 0; i < g_state_count; ++i)
        if (same(g_states[i].id, id)) return g_states[i].state;
    return CHM_SVC_DECLARED;
}

extern "C" int chimera_service_start_all(const chimera_service_manifest* services, uint32_t count,
                                           const chimera_service_ops* ops, chimera_service_plan* plan) {
    if (!ops || !ops->start || !ops->health || !plan) return -1;
    const int resolved = chimera_service_resolve(services, count, plan);
    if (resolved < 0) return resolved;
    for (uint32_t i = 0; i < count; ++i)
        (void)chimera_service_set_state(services[i].id, CHM_SVC_DECLARED);

    for (uint32_t k = 0; k < plan->count; ++k) {
        const int index = find(services, count, plan->ordered_ids[k]);
        if (index < 0) return -7;
        const chimera_service_manifest* service = &services[static_cast<uint32_t>(index)];
        if (!dependencies_running(services, static_cast<uint32_t>(index))) {
            (void)chimera_service_set_state(service->id, CHM_SVC_BLOCKED);
            if (service->critical) return -8;
            continue;
        }
        (void)chimera_service_set_state(service->id, CHM_SVC_STARTING);
        int result = run_one(service->id, ops);
        if (result < 0 && service->restart == CHM_RESTART_FAILURE) {
            (void)chimera_service_set_state(service->id, CHM_SVC_RECOVERING);
            result = run_one(service->id, ops); /* one bounded retry, never an unbounded loop */
        }
        if (result == 0) {
            (void)chimera_service_set_state(service->id, CHM_SVC_RUNNING);
        } else {
            (void)chimera_service_set_state(service->id, CHM_SVC_FAILED);
            if (service->critical) return -9;
        }
    }
    return 0;
}

extern "C" int chimera_service_stop_all(const chimera_service_manifest* services, uint32_t count,
                                          const chimera_service_ops* ops, const chimera_service_plan* plan) {
    if (!services || !ops || !ops->stop || !plan || plan->count > count) return -1;
    int result = 0;
    for (uint32_t k = plan->count; k > 0; --k) {
        const char* id = plan->ordered_ids[k - 1u];
        if (find(services, count, id) < 0) return -2;
        if (chimera_service_get_state(id) != CHM_SVC_RUNNING) continue;
        (void)chimera_service_set_state(id, CHM_SVC_STOPPING);
        if (ops->stop(id, ops->context) == 0) {
            (void)chimera_service_set_state(id, CHM_SVC_STOPPED);
        } else {
            (void)chimera_service_set_state(id, CHM_SVC_FAILED);
            result = -3;
        }
    }
    return result;
}

extern "C" void chimera_kore_bootstrap(void) {
    /* Registration is not execution. A service becomes RUNNING only through
       the callback-driven startup and independent health-check lifecycle. */
}
