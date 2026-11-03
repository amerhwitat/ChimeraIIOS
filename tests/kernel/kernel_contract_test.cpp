#include <cassert>
#include <cstddef>
#include <cstdint>
#include "chimera/interrupt.h"
#include "chimera/service.h"

int main() {
    static_assert(offsetof(chimera_interrupt_frame, vector) == 120u);
    static_assert(offsetof(chimera_interrupt_frame, cpu_frame) == 128u);

    chimera_interrupt_frame frame{};
    frame.cpu_frame[0] = 0x1111222233334444ull;
    frame.cpu_frame[1] = 0x23u;
    frame.cpu_frame[2] = 0xDEADu;
    assert(chimera_interrupt_frame_rip(&frame, 6u) == 0x1111222233334444ull);
    assert(chimera_interrupt_frame_cs(&frame, 6u) == 0x23u);
    assert(chimera_interrupt_frame_rip(&frame, 13u) == 0x23u);
    assert(chimera_interrupt_frame_cs(&frame, 13u) == 0xDEADu);
    assert(chimera_interrupt_vector_has_error_code(14u) == 1u);
    assert(chimera_interrupt_vector_has_error_code(0x80u) == 0u);

    const char* storage_deps[] = {"device"};
    chimera_service_manifest services[] = {
        {CHIMERA_SERVICE_ABI, "desktop", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 0, 1, storage_deps},
        {CHIMERA_SERVICE_ABI, "device", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 1, 0, nullptr},
        {CHIMERA_SERVICE_ABI, "storage", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 1, 1, storage_deps}
    };
    const char* ordered[3]{};
    chimera_service_plan plan{0, 3, ordered};
    assert(chimera_service_validate(services, 3) == 0);
    assert(chimera_service_resolve(services, 3, &plan) == 0);
    assert(plan.count == 3);
    assert(ordered[0] == services[1].id);
    assert(ordered[1] == services[0].id || ordered[1] == services[2].id);

    const char* cycle_a[] = {"cycle-b"};
    const char* cycle_b[] = {"cycle-a"};
    chimera_service_manifest cycle[] = {
        {CHIMERA_SERVICE_ABI, "cycle-a", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, cycle_a},
        {CHIMERA_SERVICE_ABI, "cycle-b", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, cycle_b}
    };
    assert(chimera_service_resolve(cycle, 2, &plan) == -6);
    assert(plan.count == 0);

    chimera_service_manifest null_dependencies[] = {
        {CHIMERA_SERVICE_ABI, "bad", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, nullptr}
    };
    assert(chimera_service_validate(null_dependencies, 1) == -2);
    assert(chimera_service_set_state("chimera.device", CHM_SVC_DECLARED) == 0);
    assert(chimera_service_get_state("chimera.device") == CHM_SVC_DECLARED);
    assert(chimera_service_set_state("chimera.device", CHM_SVC_RUNNING) == 0);
    assert(chimera_service_get_state("chimera.device") == CHM_SVC_RUNNING);
    assert(chimera_service_set_state("bad", 999u) == -1);
    return 0;
}
