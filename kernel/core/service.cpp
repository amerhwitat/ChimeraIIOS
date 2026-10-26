#include "../include/chimera/service.h"

namespace {
constexpr uint32_t MAX_SERVICES = CHIMERA_SERVICE_MAX;
constexpr uint32_t MAX_STATE_RECORDS = MAX_SERVICES + 8u;
struct service_state { const char* id; uint32_t state; };
struct managed_service {
    chimera_service_manifest manifest;
    uint64_t handle;
    uint32_t restart_count;
    int last_exit;
    bool started;
};
static service_state g_states[MAX_STATE_RECORDS];
static uint32_t g_state_count = 0;
static managed_service g_managed[MAX_SERVICES];
static uint32_t g_managed_count = 0;
static const chimera_service_backend* g_backend = nullptr;
static chimera_service_supervisor_config g_config{};
static const char* g_order[MAX_SERVICES];
static uint32_t g_order_count = 0;
static bool g_supervisor_active = false;

static bool same(const char* a, const char* b) {
    if (!a || !b) return false;
    while (*a && *b && *a == *b) { ++a; ++b; }
    return *a == 0 && *b == 0;
}
static bool nonempty(const char* s) { return s && *s; }
static int find(const chimera_service_manifest* s, uint32_t n, const char* id) {
    if (!s || !nonempty(id)) return -1;
    for (uint32_t i = 0; i < n; ++i) if (same(s[i].id, id)) return static_cast<int>(i);
    return -1;
}
static int find_managed(const char* id) {
    for (uint32_t i = 0; i < g_managed_count; ++i)
        if (same(g_managed[i].manifest.id, id)) return static_cast<int>(i);
    return -1;
}
static bool set_state_internal(const char* id, uint32_t state) {
    for (uint32_t i = 0; i < g_state_count; ++i) {
        if (same(g_states[i].id, id)) { g_states[i].state = state; return true; }
    }
    if (g_state_count >= MAX_STATE_RECORDS) return false;
    g_states[g_state_count++] = {id, state};
    return true;
}
static bool dependencies_running(const chimera_service_manifest* s) {
    for (uint32_t d = 0; d < s->dependency_count; ++d)
        if (chimera_service_get_state(s->dependencies[d]) != CHM_SVC_RUNNING) return false;
    return true;
}
static void wait_ticks(uint32_t ticks) {
    if (ticks && g_backend && g_backend->sleep_ticks) g_backend->sleep_ticks(ticks, g_backend->context);
}
static int start_one(managed_service* m) {
    if (!m || !g_backend || !g_backend->start || !g_backend->probe) return -1;
    if (!dependencies_running(&m->manifest)) {
        set_state_internal(m->manifest.id, CHM_SVC_BLOCKED);
        return -2;
    }
    set_state_internal(m->manifest.id, CHM_SVC_STARTING);
    for (;;) {
        uint64_t handle = 0;
        const int spawn_rc = g_backend->start(m->manifest.id, &handle, g_backend->context);
        if (spawn_rc == 0 && handle != 0) {
            m->handle = handle;
            m->started = true;
            uint32_t elapsed = 0;
            for (;;) {
                const int healthy = g_backend->probe(m->manifest.id, m->handle, g_backend->context);
                if (healthy > 0) {
                    set_state_internal(m->manifest.id, CHM_SVC_RUNNING);
                    return 0;
                }
                if (healthy < 0 || elapsed >= g_config.health_timeout_ticks) break;
                const uint32_t step = g_config.health_poll_ticks;
                if (!step) break;
                wait_ticks(step);
                if (UINT32_MAX - elapsed < step) elapsed = g_config.health_timeout_ticks;
                else elapsed += step;
            }
            /* Never forget a failed-to-stop service: doing so could orphan a
               process and allow a duplicate instance on the next retry. */
            const int stop_rc = g_backend->stop(m->manifest.id, m->handle, g_backend->context);
            if (stop_rc != 0) {
                set_state_internal(m->manifest.id, CHM_SVC_FAILED);
                return -4;
            }
            m->started = false;
            m->handle = 0;
        }
        set_state_internal(m->manifest.id, CHM_SVC_FAILED);
        if (m->manifest.restart != CHM_RESTART_FAILURE ||
            m->restart_count >= g_config.max_restarts)
            return spawn_rc != 0 ? spawn_rc : -3;
        ++m->restart_count;
        wait_ticks(g_config.restart_backoff_ticks);
        set_state_internal(m->manifest.id, CHM_SVC_RECOVERING);
    }
}
static int stop_one(managed_service* m) {
    if (!m || !m->started) return 0;
    set_state_internal(m->manifest.id, CHM_SVC_STOPPING);
    const int rc = g_backend && g_backend->stop
        ? g_backend->stop(m->manifest.id, m->handle, g_backend->context) : -1;
    if (rc == 0) {
        m->started = false;
        m->handle = 0;
        set_state_internal(m->manifest.id, CHM_SVC_STOPPED);
    } else {
        set_state_internal(m->manifest.id, CHM_SVC_FAILED);
    }
    return rc;
}
static void rollback_started() {
    for (uint32_t i = g_order_count; i > 0; --i) {
        const int index = find_managed(g_order[i - 1]);
        if (index >= 0) (void)stop_one(&g_managed[static_cast<uint32_t>(index)]);
    }
}
}

extern "C" int chimera_service_validate(const chimera_service_manifest* s, uint32_t n) {
    if (!s || !n) return -1;
    if (n > MAX_SERVICES) return -5;
    for (uint32_t i = 0; i < n; ++i) {
        if (s[i].abi_version != CHIMERA_SERVICE_ABI || !nonempty(s[i].id)) return -2;
        if (s[i].state > CHM_SVC_RECOVERING || s[i].restart > CHM_RESTART_FAILURE || s[i].critical > 1u) return -6;
        if (s[i].dependency_count && !s[i].dependencies) return -7;
        if (s[i].dependency_count >= n) return -7;
        for (uint32_t j = i + 1; j < n; ++j) if (same(s[i].id, s[j].id)) return -3;
        for (uint32_t d = 0; d < s[i].dependency_count; ++d) {
            const char* dep = s[i].dependencies[d];
            if (!nonempty(dep) || find(s, n, dep) < 0) return -4;
            if (same(s[i].id, dep)) return -6;
            for (uint32_t k = 0; k < d; ++k) if (same(s[i].dependencies[k], dep)) return -6;
        }
    }
    return 0;
}
extern "C" int chimera_service_resolve(const chimera_service_manifest* s, uint32_t n, chimera_service_plan* p) {
    if (!p) return -1;
    p->count = 0;
    if (!p->ordered_ids || !n || n > MAX_SERVICES || p->capacity < n) return -1;
    const int rc = chimera_service_validate(s, n);
    if (rc < 0) return rc;
    uint8_t done[MAX_SERVICES] = {};
    while (p->count < n) {
        bool progressed = false;
        for (uint32_t i = 0; i < n; ++i) {
            if (done[i]) continue;
            bool ready = true;
            for (uint32_t d = 0; d < s[i].dependency_count; ++d) {
                const int k = find(s, n, s[i].dependencies[d]);
                if (k < 0 || !done[static_cast<uint32_t>(k)]) { ready = false; break; }
            }
            if (ready) { done[i] = 1; p->ordered_ids[p->count++] = s[i].id; progressed = true; }
        }
        if (!progressed) { p->count = 0; return -6; }
    }
    return 0;
}
extern "C" int chimera_service_set_state(const char* id, uint32_t state) {
    if (!nonempty(id) || state > CHM_SVC_RECOVERING) return -1;
    return set_state_internal(id, state) ? 0 : -2;
}
extern "C" uint32_t chimera_service_get_state(const char* id) {
    for (uint32_t i = 0; i < g_state_count; ++i)
        if (same(g_states[i].id, id)) return g_states[i].state;
    return CHM_SVC_DECLARED;
}
extern "C" void chimera_kore_bootstrap(void) {
    /* No backend is wired into early boot yet. Never claim service health here. */
    set_state_internal("chimera.device", CHM_SVC_BLOCKED);
    set_state_internal("chimera.storage", CHM_SVC_BLOCKED);
    set_state_internal("chimera.security", CHM_SVC_BLOCKED);
    set_state_internal("chimera.logging", CHM_SVC_BLOCKED);
    set_state_internal("chimera.kore", CHM_SVC_BLOCKED);
}
extern "C" int chimera_service_supervisor_start(const chimera_service_manifest* services,
                                                uint32_t count,
                                                const chimera_service_backend* backend,
                                                const chimera_service_supervisor_config* config) {
    if (g_supervisor_active || !backend || !backend->start || !backend->probe ||
        !backend->wait_exit || !backend->stop || !config) return -1;
    if ((config->health_timeout_ticks &&
         (!config->health_poll_ticks || !backend->sleep_ticks)) ||
        (config->restart_backoff_ticks && !backend->sleep_ticks)) return -1;
    const int valid = chimera_service_validate(services, count);
    if (valid != 0) return valid;
    const chimera_service_plan plan{0u, MAX_SERVICES, g_order};
    chimera_service_plan mutable_plan = plan;
    const int resolved = chimera_service_resolve(services, count, &mutable_plan);
    if (resolved != 0) return resolved;
    g_managed_count = count;
    g_order_count = mutable_plan.count;
    g_backend = backend;
    g_config = *config;
    for (uint32_t i = 0; i < count; ++i) {
        g_managed[i] = {services[i], 0, 0, 0, false};
        if (!set_state_internal(services[i].id, CHM_SVC_DECLARED)) {
            g_managed_count = 0;
            g_order_count = 0;
            g_backend = nullptr;
            return -3;
        }
    }
    /* Store order pointers against the supervisor-owned manifest copies. */
    for (uint32_t i = 0; i < g_order_count; ++i) {
        const int index = find_managed(g_order[i]);
        if (index < 0) return -2;
        g_order[i] = g_managed[static_cast<uint32_t>(index)].manifest.id;
    }
    g_supervisor_active = true;
    for (uint32_t i = 0; i < g_order_count; ++i) {
        const int index = find_managed(g_order[i]);
        if (index < 0) { rollback_started(); g_supervisor_active = false; return -2; }
        managed_service* m = &g_managed[static_cast<uint32_t>(index)];
        const int rc = start_one(m);
        if (rc != 0 && m->manifest.critical) {
            rollback_started();
            g_supervisor_active = false;
            return rc;
        }
    }
    return 0;
}
extern "C" int chimera_service_supervisor_poll(void) {
    if (!g_supervisor_active || !g_backend || !g_backend->wait_exit) return -1;
    int failures = 0;
    for (uint32_t oi = 0; oi < g_order_count; ++oi) {
        const int index = find_managed(g_order[oi]);
        if (index < 0) { ++failures; continue; }
        managed_service* m = &g_managed[static_cast<uint32_t>(index)];
        if (!m->started) continue;
        /* A failed dependency makes this service unhealthy even if its process
           is still alive; stop dependents before continuing down the graph. */
        if (!dependencies_running(&m->manifest)) {
            if (stop_one(m) != 0) ++failures;
            else set_state_internal(m->manifest.id, CHM_SVC_BLOCKED);
            continue;
        }
        int exit_code = 0;
        const int rc = g_backend->wait_exit(m->manifest.id, m->handle, &exit_code, g_backend->context);
        if (rc < 0) {
            set_state_internal(m->manifest.id, CHM_SVC_FAILED);
            (void)stop_one(m); /* attempt cleanup, but keep the supervisor failed */
            set_state_internal(m->manifest.id, CHM_SVC_FAILED);
            ++failures;
            continue;
        }
        if (rc == 0) continue;
        m->started = false;
        m->handle = 0;
        m->last_exit = exit_code;
        set_state_internal(m->manifest.id, CHM_SVC_FAILED);
        if (m->manifest.restart == CHM_RESTART_FAILURE && m->restart_count < g_config.max_restarts &&
            dependencies_running(&m->manifest)) {
            ++m->restart_count;
            wait_ticks(g_config.restart_backoff_ticks);
            set_state_internal(m->manifest.id, CHM_SVC_RECOVERING);
            if (start_one(m) != 0) ++failures;
        } else {
            if (m->manifest.critical) ++failures;
        }
    }
    return failures ? -2 : 0;
}
extern "C" int chimera_service_supervisor_stop(void) {
    if (!g_supervisor_active) return -1;
    int failures = 0;
    for (uint32_t i = g_order_count; i > 0; --i) {
        const int index = find_managed(g_order[i - 1]);
        if (index >= 0 && stop_one(&g_managed[static_cast<uint32_t>(index)]) != 0) ++failures;
    }
    g_supervisor_active = false;
    g_backend = nullptr;
    return failures ? -2 : 0;
}
extern "C" uint32_t chimera_service_supervisor_count(void) { return g_managed_count; }
