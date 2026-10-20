#include "chimera/service.h"
#include <stdio.h>
#include <string.h>

struct fixture {
    int starts[5], health[5], stops[5];
    int fail_display_once, fail_audio_health;
    char stop_order[8][16];
    int stop_count;
};
static int index_of(const char* id) {
    if (!strcmp(id, "console")) return 0;
    if (!strcmp(id, "display")) return 1;
    if (!strcmp(id, "ui")) return 2;
    if (!strcmp(id, "audio")) return 3;
    if (!strcmp(id, "media")) return 4;
    return -1;
}
static int start_service(const char* id, void* opaque) {
    fixture* f = static_cast<fixture*>(opaque);
    const int i = index_of(id);
    if (i < 0) return -1;
    ++f->starts[i];
    if (i == 1 && f->fail_display_once) { f->fail_display_once = 0; return -1; }
    return 0;
}
static int health_service(const char* id, void* opaque) {
    fixture* f = static_cast<fixture*>(opaque);
    const int i = index_of(id);
    if (i < 0) return -1;
    ++f->health[i];
    return i == 3 && f->fail_audio_health ? -1 : 0;
}
static int stop_service(const char* id, void* opaque) {
    fixture* f = static_cast<fixture*>(opaque);
    const int i = index_of(id);
    if (i < 0) return -1;
    ++f->stops[i];
    if (f->stop_count < 8) {
        snprintf(f->stop_order[f->stop_count], sizeof(f->stop_order[f->stop_count]), "%s", id);
        ++f->stop_count;
    }
    return 0;
}
static int position(const char* const* order, uint32_t count, const char* id) {\n    for (uint32_t i = 0; i < count; ++i) if (!strcmp(order[i], id)) return static_cast<int>(i);\n    return -1;\n}\nstatic int check(bool ok, const char* what) {
    if (!ok) fprintf(stderr, "FAIL: %s\n", what);
    return ok ? 0 : 1;
}
int main() {
    const char* display_deps[] = {"console"};
    const char* ui_deps[] = {"display"};
    const char* media_deps[] = {"audio"};
    chimera_service_manifest services[] = {
        {CHIMERA_SERVICE_ABI, "ui", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 1, 1, ui_deps},
        {CHIMERA_SERVICE_ABI, "display", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 1, 1, display_deps},
        {CHIMERA_SERVICE_ABI, "console", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 1, 0, nullptr},
        {CHIMERA_SERVICE_ABI, "audio", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 0, nullptr},
        {CHIMERA_SERVICE_ABI, "media", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, media_deps}
    };
    const char* ordered[CHIMERA_SERVICE_MAX] = {};
    chimera_service_plan plan{0, CHIMERA_SERVICE_MAX, ordered};
    fixture f{};
    f.fail_display_once = 1;
    f.fail_audio_health = 1;
    chimera_service_ops ops{start_service, health_service, stop_service, &f};
    int failures = 0;

    chimera_kore_bootstrap();\n    failures += check(chimera_service_get_state("chimera.storage") == CHM_SVC_DECLARED,\n                      "Kore bootstrap does not fabricate storage service readiness");\n    failures += check(chimera_service_validate(services, 5) == 0, "valid service manifest");
    failures += check(chimera_service_start_all(services, 5, &ops, &plan) == 0,
                      "noncritical failure does not abort unrelated services");
    failures += check(plan.count == 5 && !strcmp(ordered[0], "console") &&
                      !strcmp(ordered[1], "display") && !strcmp(ordered[2], "ui"),
                      "dependency order is respected");
    failures += check(f.starts[1] == 2 &&
                      chimera_service_get_state("display") == CHM_SVC_RUNNING,
                      "failure restart is bounded and health-checked");
    failures += check(chimera_service_get_state("ui") == CHM_SVC_RUNNING,
                      "dependent starts only after dependency is healthy");
    failures += check(chimera_service_get_state("audio") == CHM_SVC_FAILED &&
                      chimera_service_get_state("media") == CHM_SVC_BLOCKED,
                      "failed health blocks dependent service");

    f.stop_count = 0;
    failures += check(chimera_service_stop_all(services, 5, &ops, &plan) == 0,
                      "shutdown succeeds");
    failures += check(chimera_service_get_state("console") == CHM_SVC_STOPPED &&
                      chimera_service_get_state("display") == CHM_SVC_STOPPED,
                      "shutdown transitions running services to stopped");
    failures += check(f.stop_count >= 3 && !strcmp(f.stop_order[0], "ui") &&
                      !strcmp(f.stop_order[1], "display") &&
                      !strcmp(f.stop_order[2], "console"),
                      "shutdown uses reverse dependency order");
    if (failures) return 1;
    puts("PASS: service lifecycle, dependency, health, retry and shutdown tests");
    return 0;
}
